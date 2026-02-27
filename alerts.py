from fastapi import APIRouter, Depends, BackgroundTasks
from datetime import datetime, timedelta
from app.database import transactions_collection, alerts_collection
from app.auth import get_current_user
from bson import ObjectId

router = APIRouter()


async def generate_alerts_for_user(user_id: str):
    """
    Background task that scans transactions and creates alerts.
    Runs after CSV upload or on demand.
    """
    now = datetime.utcnow()
    new_alerts = []

    # 1. Renewal reminders (subscriptions due in next 3 days)
    cursor = transactions_collection.find({
        "user_id": user_id,
        "is_subscription": True
    })
    txns = await cursor.to_list(length=500)

    from ml.engine import SubscriptionDetector
    detector = SubscriptionDetector()

    merchant_seen = {}
    for t in txns:
        m = t["merchant"].lower()
        if m not in merchant_seen or t["date"] > merchant_seen[m]["date"]:
            merchant_seen[m] = t

    for m, t in merchant_seen.items():
        recurrence = t.get("recurrence_type", "monthly")
        next_charge = detector.get_next_charge_date(t["date"], recurrence)
        if next_charge:
            days_left = (next_charge - now).days
            if 0 <= days_left <= 3:
                new_alerts.append({
                    "user_id": user_id,
                    "alert_type": "renewal_reminder",
                    "message": f"⏰ {t['merchant']} will charge ₹{t['amount']} in {days_left} day(s).",
                    "merchant": t["merchant"],
                    "amount": t["amount"],
                    "is_read": False,
                    "created_at": now
                })

    # 2. Micro-spend warning (if this week's micro spend > threshold)
    week_start = now - timedelta(days=7)
    micro_cursor = transactions_collection.find({
        "user_id": user_id,
        "is_micro_spend": True,
        "date": {"$gte": week_start}
    })
    micro_txns = await micro_cursor.to_list(length=200)
    micro_total = sum(t.get("amount", 0) for t in micro_txns)

    if micro_total > 1000:
        new_alerts.append({
            "user_id": user_id,
            "alert_type": "micro_spend_warning",
            "message": f"⚠️ You've spent ₹{micro_total:.0f} on small transactions this week. That's ₹{micro_total * 52:.0f}/year!",
            "amount": micro_total,
            "is_read": False,
            "created_at": now
        })

    # 3. Anomaly alerts
    anomaly_cursor = transactions_collection.find({
        "user_id": user_id,
        "is_anomaly": True,
        "date": {"$gte": now - timedelta(days=1)}
    })
    anomaly_txns = await anomaly_cursor.to_list(length=50)
    for a in anomaly_txns:
        new_alerts.append({
            "user_id": user_id,
            "alert_type": "anomaly_detected",
            "message": f"🚨 Unusual charge of ₹{a['amount']} detected at {a['merchant']}. Please verify.",
            "merchant": a["merchant"],
            "amount": a["amount"],
            "is_read": False,
            "created_at": now
        })

    if new_alerts:
        await alerts_collection.insert_many(new_alerts)


@router.post("/generate")
async def trigger_alert_generation(
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user)
):
    """Trigger background alert generation."""
    user_id = str(current_user["_id"])
    background_tasks.add_task(generate_alerts_for_user, user_id)
    return {"message": "Alert generation started in background"}


@router.get("/")
async def get_alerts(
    unread_only: bool = False,
    current_user=Depends(get_current_user)
):
    """Get all alerts for the current user."""
    user_id = str(current_user["_id"])
    query = {"user_id": user_id}
    if unread_only:
        query["is_read"] = False

    cursor = alerts_collection.find(query).sort("created_at", -1).limit(50)
    alerts = await cursor.to_list(length=50)

    for a in alerts:
        a["_id"] = str(a["_id"])

    unread_count = await alerts_collection.count_documents({"user_id": user_id, "is_read": False})

    return {
        "alerts": alerts,
        "unread_count": unread_count
    }


@router.patch("/{alert_id}/read")
async def mark_alert_read(
    alert_id: str,
    current_user=Depends(get_current_user)
):
    """Mark an alert as read."""
    await alerts_collection.update_one(
        {"_id": ObjectId(alert_id), "user_id": str(current_user["_id"])},
        {"$set": {"is_read": True}}
    )
    return {"message": "Alert marked as read"}


@router.patch("/mark-all-read")
async def mark_all_read(current_user=Depends(get_current_user)):
    """Mark all alerts as read."""
    result = await alerts_collection.update_many(
        {"user_id": str(current_user["_id"])},
        {"$set": {"is_read": True}}
    )
    return {"message": f"{result.modified_count} alerts marked as read"}


@router.delete("/{alert_id}")
async def delete_alert(alert_id: str, current_user=Depends(get_current_user)):
    await alerts_collection.delete_one({
        "_id": ObjectId(alert_id),
        "user_id": str(current_user["_id"])
    })
    return {"message": "Alert deleted"}
