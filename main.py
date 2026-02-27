from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app import transactions, subscriptions, analytics, auth, alerts

app = FastAPI(
    title="SheTech - Financial Leak Detection API",
    description="AI-powered subscription and micro-spending leakage detection system",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(transactions.router, prefix="/api/transactions", tags=["Transactions"])
app.include_router(subscriptions.router, prefix="/api/subscriptions", tags=["Subscriptions"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["Alerts"])

@app.get("/")
def root():
    return {"message": "SheTech Financial Leak Detection API", "status": "running"}
