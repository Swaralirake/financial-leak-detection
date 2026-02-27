from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class SpendingCategory(str, Enum):
    SUBSCRIPTION = "subscription"
    MICRO_SPEND = "micro_spend"
    ESSENTIAL = "essential"
    UNNECESSARY = "unnecessary"
    UNKNOWN = "unknown"


class RecurrenceType(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    IRREGULAR = "irregular"
    NONE = "none"


class Transaction(BaseModel):
    id: Optional[str] = None
    user_id: str
    date: datetime
    amount: float
    merchant: str
    description: str
    category: Optional[SpendingCategory] = SpendingCategory.UNKNOWN
    recurrence_type: Optional[RecurrenceType] = RecurrenceType.NONE
    is_subscription: bool = False
    is_micro_spend: bool = False
    is_wasteful: Optional[bool] = None
    leak_score_contribution: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Subscription(BaseModel):
    id: Optional[str] = None
    user_id: str
    merchant: str
    amount: float
    recurrence_type: RecurrenceType
    last_charged: datetime
    next_charge_estimated: Optional[datetime] = None
    is_active: bool = True
    usage_score: float = 1.0  # 0 = never used, 1 = frequently used
    annual_cost: float = 0.0
    is_recommended_to_cancel: bool = False
    detected_at: datetime = Field(default_factory=datetime.utcnow)


class User(BaseModel):
    id: Optional[str] = None
    name: str
    email: str
    hashed_password: str
    monthly_budget: Optional[float] = None
    financial_leak_score: float = 0.0  # 0-100 (lower = healthier)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Alert(BaseModel):
    id: Optional[str] = None
    user_id: str
    alert_type: str  # "renewal_reminder", "micro_spend_warning", "leak_detected"
    message: str
    merchant: Optional[str] = None
    amount: Optional[float] = None
    is_read: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)


class FinancialLeakReport(BaseModel):
    user_id: str
    total_monthly_leak: float
    total_annual_leak: float
    financial_leak_score: float
    subscriptions_count: int
    active_subscriptions_cost: float
    micro_spend_monthly: float
    unnecessary_spend_monthly: float
    top_drains: List[dict]
    recommendations: List[str]
    generated_at: datetime = Field(default_factory=datetime.utcnow)
