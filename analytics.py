from fastapi import APIRouter, Depends, Query
from datetime import datetime, timedelta
from app.database import transactions_collection, users_collection
from app.auth import get_current_user
from ml.engine import (
    FinancialLeakScoreCalculator,
    AnnualLossPredictor,
    MicroSpendDetector
)
from bson import ObjectId

router = APIRouter()

score_calculator = FinancialLeakScoreCalculator()
loss_predictor = AnnualLossPredictor()
micro_detector = MicroSpendDetector()


@router.get("/financial-leak-score")
async def get_financial_leak_score(
    months: int = Query(3, ge=1, le=12),
    current_user=Depends(get_current_user)
):
    """
    Calculate and return the Financial Leak Score for the user.
    Score: 0-100. Lower = healthier spending habits.
    """
    user_id = str(current_user["_id"])
    since = datetime.utcnow() - timedelta(days=30 * months)

    cursor = transactions_collection.find({"user_id": user_id, "date": {"$gte": since}})
    transactions = await cursor.to_list(length=1000)

    txns = []
    for t in transactions:
        txns.append({
            "amount": t.get("amount", 0),
            "date": t.get("date", datetime.utcnow()).isoformat(),
            "is_subscription": t.get("is_subscription", False),
            "is_micro_spend": t.get("is_micro_spend", False),
            "is_wasteful": t.get("is_wasteful", False),
            "is_anomaly": t.get("is_anomaly", False),
        })

    score_data = score_calculator.calculate(txns, current_user.get("monthly_budget"))

    # Update user's score in DB
    await users_collection.update_one(
        {"_id": current_user["_id"]},
        {"$set": {"financial_leak_score": score_data["score"]}}
    )

    return score_data


@router.get("/annual-prediction")
async def get_annual_loss_prediction(
    current_user=Depends(get_current_user)
):
    """Predict annual financial leakage based on current spending trends."""
    user_id = str(current_user["_id"])
    since = datetime.utcnow() - timedelta(days=180)  # 6 months history

    cursor = transactions_collection.find({"user_id": user_id, "date": {"$gte": since}})
    transactions = await cursor.to_list(length=2000)

    txns = [
        {
            "amount": t.get("amount", 0),
            "date": t.get("date", datetime.utcnow()).isoformat(),
            "is_subscription": t.get("is_subscription", False),
            "is_micro_spend": t.get("is_micro_spend", False),
            "is_wasteful": t.get("is_wasteful", False),
        }
        for t in transactions
    ]

    prediction = loss_predictor.predict(txns)
    return prediction


@router.get("/micro-spend-analysis")
async def get_micro_spend_analysis(
    months: int = Query(1, ge=1, le=6),
    current_user=Depends(get_current_user)
):
    """Analyze micro-spending patterns."""
    user_id = str(current_user["_id"])
    since = datetime.utcnow() - timedelta(days=30 * months)

    cursor = transactions_collection.find({
        "user_id": user_id,
        "date": {"$gte": since},
        "is_micro_spend": True
    })
    micro_txns = await cursor.to_list(length=500)

    # Group by merchant
    merchant_totals = {}
    for t in micro_txns:
        m = t.get("merchant", "Unknown")
        merchant_totals[m] = merchant_totals.get(m, 0) + t.get("amount", 0)

    top_merchants = sorted(merchant_totals.items(), key=lambda x: x[1], reverse=True)[:10]

    total = sum(t.get("amount", 0) for t in micro_txns)

    return {
        "total_micro_spend": round(total, 2),
        "transaction_count": len(micro_txns),
        "daily_average": round(total / (30 * months), 2),
        "annual_projection": round(total / months * 12, 2),
        "top_merchants": [{"merchant": m, "total": round(v, 2)} for m, v in top_merchants]
    }


@router.get("/spending-breakdown")
async def get_spending_breakdown(
    months: int = Query(1, ge=1, le=12),
    current_user=Depends(get_current_user)
):
    """Get categorized spending breakdown with leak percentages."""
    user_id = str(current_user["_id"])
    since = datetime.utcnow() - timedelta(days=30 * months)

    pipeline = [
        {"$match": {"user_id": user_id, "date": {"$gte": since}}},
        {"$group": {
            "_id": "$category",
            "total": {"$sum": "$amount"},
            "count": {"$sum": 1}
        }}
    ]

    results = await transactions_collection.aggregate(pipeline).to_list(length=20)
    total_spend = sum(r["total"] for r in results)

    breakdown = [
        {
            "category": r["_id"] or "unknown",
            "total": round(r["total"], 2),
            "count": r["count"],
            "percentage": round(r["total"] / max(total_spend, 1) * 100, 1)
        }
        for r in results
    ]

    breakdown.sort(key=lambda x: x["total"], reverse=True)
    return {"breakdown": breakdown, "total_spend": round(total_spend, 2)}


@router.get("/full-report")
async def get_full_leak_report(current_user=Depends(get_current_user)):
    """Generate a comprehensive financial leak report."""
    user_id = str(current_user["_id"])
    since = datetime.utcnow() - timedelta(days=90)

    cursor = transactions_collection.find({"user_id": user_id, "date": {"$gte": since}})
    transactions = await cursor.to_list(length=2000)

    total_spend = sum(t.get("amount", 0) for t in transactions)
    sub_spend = sum(t.get("amount", 0) for t in transactions if t.get("is_subscription"))
    micro_spend = sum(t.get("amount", 0) for t in transactions if t.get("is_micro_spend"))
    wasteful_spend = sum(t.get("amount", 0) for t in transactions if t.get("is_wasteful"))

    # Top drains
    merchant_totals = {}
    for t in transactions:
        m = t.get("merchant", "Unknown")
        merchant_totals[m] = merchant_totals.get(m, 0) + t.get("amount", 0)
    top_drains = sorted(merchant_totals.items(), key=lambda x: x[1], reverse=True)[:5]

    # Generate recommendations
    recommendations = []
    if sub_spend > total_spend * 0.3:
        recommendations.append("🔴 Your subscriptions exceed 30% of your total spending. Review and cancel unused ones.")
    if micro_spend > 2000:
        recommendations.append("🟠 You're spending ₹{:.0f} monthly on small transactions. Consider setting a daily limit.".format(micro_spend / 3))
    if wasteful_spend > total_spend * 0.2:
        recommendations.append("🟡 Over 20% of your spending is classified as unnecessary. Track and reduce impulse purchases.")
    if not recommendations:
        recommendations.append("🟢 Your spending looks healthy! Keep maintaining your financial discipline.")

    monthly_leak = (sub_spend + micro_spend + wasteful_spend) / 3
    annual_leak = monthly_leak * 12

    return {
        "report_period": "Last 90 days",
        "total_spend": round(total_spend, 2),
        "monthly_leak_estimate": round(monthly_leak, 2),
        "annual_leak_estimate": round(annual_leak, 2),
        "subscription_spend": round(sub_spend, 2),
        "micro_spend": round(micro_spend, 2),
        "unnecessary_spend": round(wasteful_spend, 2),
        "top_drains": [{"merchant": m, "total": round(v, 2)} for m, v in top_drains],
        "recommendations": recommendations,
        "generated_at": datetime.utcnow().isoformat()
    }
