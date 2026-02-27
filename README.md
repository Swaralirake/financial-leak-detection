# Micro-Spending-leakage

# Financial Leak Detector

Most people lose money every month without realizing it.

Unused subscriptions.  
Small daily spends that quietly add up.  
Random transactions that don’t look normal.

This project is a backend system built with FastAPI that analyzes transaction data and tries to detect those “financial leaks”.

It’s structured like a production-style API, with modular ML logic separated from route handling, so it can scale into a full product later.

---

## What It Does

- Detects recurring subscriptions
- Identifies micro-spending patterns
- Classifies expenses
- Flags unusual or abnormal transactions
- Calculates a Financial Leak Score
- Predicts potential annual financial loss

The current ML logic is rule-based, but the architecture is designed so real machine learning models can be plugged in easily.

---

## Tech Stack

- Python
- FastAPI
- Uvicorn
- Pydantic
- Modular ML engine design

---

## Project Structure

financial-leak-backend/

- app/ → API routes and request handling  
  - main.py  
  - analytics.py  
  - transactions.py  
  - subscriptions.py  
  - auth.py  
  - alerts.py  

- ml/ → Financial analysis engine  
  - engine.py  

- requirements.txt  
- README.md  

The `ml/engine.py` file contains the detection and scoring logic.  
The `app/` folder handles API endpoints and connects everything together.

---

## How to Run Locally

1. Clone the repository  
2. Create a virtual environment  
3. Install dependencies  

pip install -r requirements.txt  

4. Start the server  

uvicorn app.main:app --reload  

Then open:

http://127.0.0.1:8000/docs  

to test the API using Swagger UI.

---

## Why I Built This

This project is part of a larger idea to build tools that help people understand where their money actually goes.

It also helped me practice:
- Backend architecture
- API design
- Structuring ML-driven systems
- Debugging real-world import and dependency issues
- Organizing a scalable project layout

---

## Next Steps

- Connect a frontend dashboard
- Improve scoring logic
- Integrate real ML models
- Deploy to the cloud
- Add real transaction datasets

---

Still building. Still improving.
