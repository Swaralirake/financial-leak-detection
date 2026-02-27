from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta
from app.database import transactions_collection, users_collection
from app.auth import get_current_user
from ml.engine import (
    SubscriptionDetector, MicroSpendDetector,
    ExpenseClassifier, AnomalyDetector
)
from bson import ObjectId
import pandas as pd
import io

router = APIRouter()

subscription_detector = SubscriptionDetector()
micro_spend_detector = MicroSpendDetector()
expense_classifier = ExpenseClassifier()
anomaly_detector = AnomalyDetector()


def serialize_txn(txn: dict) -> dict:
    txn["_id"] = str(txn["_id"])
    return txn


@router.post("/upload-csv")
async def upload_transactions_csv(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user)
):
    """
    Upload bank statement CSV file.
    Expected columns: date, amount, merchant, description
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    content = await file.read()
    df = pd.read_csv(io.StringIO(content.decode("utf-8")))

    required_cols = {"date", "amount", "merchant", "description"}
    if not required_cols.issubset(df.columns):
        raise HTTPException(
            status_code=400,
            detail=f"CSV must contain columns: {required_cols}"
        )

    df["date"] = pd.to_datetime(df["date"])
    transactions = df.to_dict("records")

    # Run ML pipeline
    transactions = subscription_detector.detect(transactions)
    transactions = micro_spend_detector.detect(transactions)
    transactions = expense_classifier.classify(transactions)
    transactions = anomaly_detector.detect(transactions)

    # Add user_id and save
    user_id = str(current_user["_id"])
    docs = []
    for txn in transactions:
        txn["user_id"] = user_id
        txn["date"] = pd.to_datetime(txn["date"]).to_pydatetime()
        txn["created_at"] = datetime.utcnow()
        docs.append(txn)

    if docs:
        await transactions_collection.insert_many(docs)

    return {
        "message": f"✅ {len(docs)} transactions processed and saved",
        "subscriptions_detected": sum(1 for t in docs if t.get("is_subscription")),
        "micro_spends_detected": sum(1 for t in docs if t.get("is_micro_spend")),
        "anomalies_detected": sum(1 for t in docs if t.get("is_anomaly")),
    }


@router.post("/add")
async def add_transaction(
    transaction: dict,
    current_user=Depends(get_current_user)
):
    """Manually add a single transaction."""
    user_id = str(current_user["_id"])
    transaction["user_id"] = user_id
    transaction["date"] = datetime.fromisoformat(transaction["date"])
    transaction["created_at"] = datetime.utcnow()

    # Run ML on single transaction
    processed = subscription_detector.detect([transaction])
    processed = micro_spend_detector.detect(processed)
    processed = expense_classifier.classify(processed)
    processed = anomaly_detector.detect(processed)

    result = await transactions_collection.insert_one(processed[0])
    return {"message": "Transaction added", "id": str(result.inserted_id)}


@router.get("/")
async def get_transactions(
    page: int = Query(1, ge=1),
    limit: int = Query(20, le=100),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    category: Optional[str] = None,
    is_subscription: Optional[bool] = None,
    is_micro_spend: Optional[bool] = None,
    current_user=Depends(get_current_user)
):
    """Get paginated transactions with optional filters."""
    user_id = str(current_user["_id"])
    query = {"user_id": user_id}

    if start_date:
        query["date"] = {"$gte": datetime.fromisoformat(start_date)}
    if end_date:
        query.setdefault("date", {})["$lte"] = datetime.fromisoformat(end_date)
    if category:
        query["category"] = category
    if is_subscription is not None:
        query["is_subscription"] = is_subscription
    if is_micro_spend is not None:
        query["is_micro_spend"] = is_micro_spend

    skip = (page - 1) * limit
    cursor = transactions_collection.find(query).sort("date", -1).skip(skip).limit(limit)
    txns = await cursor.to_list(length=limit)
    total = await transactions_collection.count_documents(query)

    return {
        "transactions": [serialize_txn(t) for t in txns],
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit
    }


@router.get("/summary")
async def get_transaction_summary(
    months: int = Query(1, ge=1, le=12),
    current_user=Depends(get_current_user)
):
    """Get spending summary for the past N months."""
    user_id = str(current_user["_id"])
    since = datetime.utcnow() - timedelta(days=30 * months)

    pipeline = [
        {"$match": {"user_id": user_id, "date": {"$gte": since}}},
        {"$group": {
            "_id": None,
            "total_spent": {"$sum": "$amount"},
            "subscription_total": {
                "$sum": {"$cond": [{"$eq": ["$is_subscription", True]}, "$amount", 0]}
            },
            "micro_spend_total": {
                "$sum": {"$cond": [{"$eq": ["$is_micro_spend", True]}, "$amount", 0]}
            },
            "unnecessary_total": {
                "$sum": {"$cond": [{"$eq": ["$is_wasteful", True]}, "$amount", 0]}
            },
            "transaction_count": {"$sum": 1}
        }}
    ]

    result = await transactions_collection.aggregate(pipeline).to_list(length=1)

    if not result:
        return {"total_spent": 0, "subscription_total": 0, "micro_spend_total": 0}

    summary = result[0]
    summary.pop("_id", None)
    return summary


@router.delete("/{transaction_id}")
async def delete_transaction(
    transaction_id: str,
    current_user=Depends(get_current_user)
):
    user_id = str(current_user["_id"])
    result = await transactions_collection.delete_one({
        "_id": ObjectId(transaction_id),
        "user_id": user_id
    })
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"message": "Transaction deleted"}
