# Micro-Spending-leakage

# 💸 Financial Leak Detector API
An AI-powered backend system that detects hidden financial leaks such as unused subscriptions, micro-spends, anomalies, and predicts annual loss.
## 🚀 Features

- 🔍 Subscription Detection
- 💰 Micro-Spend Detection
- 📊 Expense Classification
- 🚨 Anomaly Detection
- 📈 Financial Leak Score Calculation
- 📅 Annual Loss Prediction
- 🔐 Authentication System
- 📄 Interactive API Documentation (Swagger UI)

- ## 🛠 Tech Stack

- Python
- FastAPI
- Uvicorn
- Pydantic
- Custom ML Logic Engine

- ## 📂 Project Structure

financial-leak-backend/
│
├── app/
│   ├── main.py
│   ├── analytics.py
│   ├── transactions.py
│   ├── subscriptions.py
│   ├── auth.py
│   ├── alerts.py
│
├── ml/
│   └── engine.py
│
├── requirements.txt
└── README.md

## ⚙️ Installation

1. Clone the repository:
   git clone https://github.com/yourusername/financial-leak-backend.git

2. Navigate into the folder:
   cd financial-leak-backend

3. Create virtual environment:
   python -m venv venv

4. Activate virtual environment:
   venv\Scripts\activate   (Windows)

5. Install dependencies:
   pip install -r requirements.txt

6. Run the server:
   uvicorn app.main:app --reload

   ## 📘 API Documentation

Once the server is running, access interactive API docs at:

http://127.0.0.1:8000/docs

## 🧠 How It Works

The system analyzes transaction data to:

- Identify recurring subscription charges
- Detect micro-spending patterns
- Classify expenses into categories
- Flag unusual or anomalous transactions
- Calculate a Financial Leak Score
- Predict potential annual financial loss

- ## 📌 Future Improvements

- Real ML model integration
- Bank API integration
- Dashboard frontend
- Real-time alerts
- Cloud deployment

- ## 🌐 Live Demo

Backend API: (http://127.0.0.1:8000/docs)
