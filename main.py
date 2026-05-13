from fastapi import FastAPI, BackgroundTasks
from app.services.log_service import load_logs
from app.services.ai_service import analyze_logs
from app.services.knowledge_service import find_known_issue
from app.services.severity_service import classify_severity
from app.services.db_service import init_db, save_incident, find_similar_incident, get_incidents
from app.models.incident_models import IncidentResponse
import time

app = FastAPI()
init_db()


@app.get("/")
def home():
    return {"status": "AI Troubleshooter Online"}


@app.get("/analyze", response_model=IncidentResponse)
async def analyze(background_tasks: BackgroundTasks):

    start = time.time()
    logs = load_logs()

    logs = logs[:2]

    known_issue = find_known_issue(logs)
    severity = classify_severity(logs)
    similar_incident = find_similar_incident(logs)

    result = await analyze_logs(logs, known_issue)
    import uuid

    incident_id = str(uuid.uuid4())

    background_tasks.add_task(
        save_incident,
        logs,
        severity,
        result,
        incident_id
    )

    duration = time.time() - start
    return {
        "incident_id": incident_id,
        "severity": severity,
        "known_issue": known_issue,
        "similar_incident": similar_incident,
        "analysis": result,
        "response_time": duration
    }

@app.get("/incidents")
def incidents():

    incidents = get_incidents()

    return {
        "incidents": incidents
    }

@app.get("/health")
def health():

    return {
        "status": "healthy"
    }