class SubscriptionDetector:
    def detect(self, data):
        return {"message": "Subscription detection running", "data": data}


class MicroSpendDetector:
    def detect(self, data):
        return {"message": "Micro spend detection running", "data": data}


class ExpenseClassifier:
    def classify(self, data):
        return {"message": "Expense classification running", "data": data}


class AnomalyDetector:
    def detect(self, data):
        return {"message": "Anomaly detection running", "data": data}


class FinancialLeakScoreCalculator:
    def calculate(self, data):
        return {
            "score": 75,
            "risk_level": "Medium",
            "message": "Financial leak score calculated successfully"
        }


class AnnualLossPredictor:
    def predict(self, data):
        return {
            "predicted_annual_loss": 1200,
            "message": "Annual loss predicted successfully"
        }