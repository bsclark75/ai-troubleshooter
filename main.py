from fastapi import FastAPI

from app.services.log_service import load_logs
from app.services.ai_service import analyze_logs

app = FastAPI()


@app.get("/")
def home():
    return {"status": "AI Troubleshooter Online"}


@app.get("/analyze")
def analyze():

    print("Loading logs...")

    logs = load_logs()
    logs = logs[:2]

    print("Logs loaded")

    result = analyze_logs(logs)

    print("Analysis complete")

    return {
        "analysis": result
    }