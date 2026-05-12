from fastapi import FastAPI
from app.services.log_service import load_logs
from app.services.ai_service import analyze_logs
from app.services.knowledge_service import find_known_issue
from app.services.severity_service import classify_severity

app = FastAPI()


@app.get("/")
def home():
    return {"status": "AI Troubleshooter Online"}


@app.get("/analyze")
def analyze():

    logs = load_logs()

    logs = logs[:2]

    known_issue = find_known_issue(logs)
    severity = classify_severity(logs)

    result = analyze_logs(logs, known_issue)

    return {
        "severity": severity,
        "known_issue": known_issue,
        "analysis": result
    }