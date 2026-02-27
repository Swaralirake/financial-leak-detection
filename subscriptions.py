from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from typing import List
from app.database import transactions_collection, subscriptions_collection
from app.auth import get_current_user
from ml.engine import SubscriptionDetector
from bson import ObjectId

router = APIRouter()
detector = SubscriptionDetector()


@router.get("/")
async def get_subscriptions(current_user=Depends(get_current_user)):
    """Get all detected active subscriptions for a user."""
    user_id = str(current_user["_id"])

    # Fetch subscription transactions
    cursor = transactions_collection.find({
        "user_id": user_id,
        "is_subscription": True
    })
    txns = await cursor.to_list(length=500)

    # Group by merchant to build subscription list
    merchant_map = {}
    for txn in txns:
        m = txn["merchant"].lower().strip()
        if m not in merchant_map:
            merchant_map[m] = {
                "merchant": txn["merchant"],
                "amount": txn["amount"],
                "recurrence_type": txn.get("recurrence_type", "monthly"),
                "last_charged": txn["date"],
                "charges": [txn["amount"]],
                "count": 1
            }
        else:
            merchant_map[m]["count"] += 1
            merchant_map[m]["charges"].append(txn["amount"])
            if txn["date"] > merchant_map[m]["last_charged"]:
                merchant_map[m]["last_charged"] = txn["date"]

    subscriptions = []
    for m, data in merchant_map.items():
        recurrence = data["recurrence_type"]
        next_charge = detector.get_next_charge_date(data["last_charged"], recurrence)

        # Calculate annual cost
        multiplier = {"daily": 365, "weekly": 52, "monthly": 12, "yearly": 1}.get(recurrence, 12)
        annual = data["amount"] * multiplier

        # Recommend cancellation if only 1 charge or very irregular
        recommend_cancel = data["count"] == 1 or (data["count"] < 3 and annual > 500)

        subscriptions.append({
            "merchant": data["merchant"],
            "amount": data["amount"],
            "recurrence_type": recurrence,
            "last_charged": data["last_charged"].isoformat(),
            "next_charge_estimated": next_charge.isoformat() if next_charge else None,
            "annual_cost": round(annual, 2),
            "is_recommended_to_cancel": recommend_cancel,
            "charge_count": data["count"]
        })

    # Sort by annual cost descending
    subscriptions.sort(key=lambda x: x["annual_cost"], reverse=True)

    total_annual = sum(s["annual_cost"] for s in subscriptions)
    total_monthly = total_annual / 12

    return {
        "subscriptions": subscriptions,
        "count": len(subscriptions),
        "total_monthly_cost": round(total_monthly, 2),
        "total_annual_cost": round(total_annual, 2),
        "cancellation_recommendations": [
            s for s in subscriptions if s["is_recommended_to_cancel"]
        ]
    }


@router.get("/upcoming-renewals")
async def get_upcoming_renewals(
    days_ahead: int = 7,
    current_user=Depends(get_current_user)
):
    """Get subscriptions renewing within the next N days."""
    user_id = str(current_user["_id"])
    subs_data = await get_subscriptions(current_user)
    subs = subs_data["subscriptions"]

    now = datetime.utcnow()
    upcoming = []
    for s in subs:
        if s.get("next_charge_estimated"):
            next_dt = datetime.fromisoformat(s["next_charge_estimated"])
            delta = (next_dt - now).days
            if 0 <= delta <= days_ahead:
                s["days_until_renewal"] = delta
                upcoming.append(s)

    return {
        "upcoming_renewals": sorted(upcoming, key=lambda x: x["days_until_renewal"]),
        "count": len(upcoming),
        "total_amount_due": sum(s["amount"] for s in upcoming)
    }


@router.get("/savings-potential")
async def get_savings_potential(current_user=Depends(get_current_user)):
    """Calculate potential savings if recommended subscriptions are cancelled."""
    subs_data = await get_subscriptions(current_user)
    cancellations = subs_data["cancellation_recommendations"]

    monthly_savings = sum(s["amount"] for s in cancellations)
    annual_savings = sum(s["annual_cost"] for s in cancellations)

    return {
        "subscriptions_to_cancel": len(cancellations),
        "monthly_savings_potential": round(monthly_savings, 2),
        "annual_savings_potential": round(annual_savings, 2),
        "recommendations": cancellations
    }
