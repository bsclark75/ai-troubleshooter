from fastapi import FastAPI
from app.services.log_service import load_logs
from app.services.parser_service import parse_log, summarize_logs
from app.services.ai_service import analyze_logs

app = FastAPI()

@app.get("/")
def home():
    return {"status": "AI Troubleshooter Online"}

@app.get("/logs")
def get_logs():
    logs = load_logs()
    return {"logs": logs}

@app.get("/parsed-logs")
def get_parsed_logs():
    logs = load_logs()
    parsed = [parse_log(log) for log in logs]

    return {"parsed_logs": parsed}

@app.get("/summary")
def get_summary():
    logs = load_logs()
    parsed = [parse_log(log) for log in logs]

    summary = summarize_logs(parsed)

    return summary

@app.get("/analyze")
def analyze():

    logs = load_logs()

    result = analyze_logs(logs)

    return {
        "analysis": result
    }