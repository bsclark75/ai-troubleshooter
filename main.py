from fastapi import FastAPI, BackgroundTasks, Request
from app.services.log_service import load_logs
from app.services.severity_service import classify_severity
from app.services.db_service import init_db, save_incident, get_incidents
from app.models.incident_models import IncidentResponse
from app.services.log_parser_service import parse_logs, group_incidents
from app.services.metrics_service import generate_metrics
from app.services.trend_service import analyze_trends
from app.services.incident_processor import process_incident
from fastapi.templating import Jinja2Templates
from app.services.queue_service import add_to_queue, get_queue
import time
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()
init_db()
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def dashboard_ui(request: Request):
    logs = load_logs()

    parsed_logs = parse_logs(logs)

    grouped = group_incidents(parsed_logs)

    results = []

    host_frequency = {}

    for host, incidents in grouped.items():

        severity = classify_severity(
            [incident["raw"] for incident in incidents]
        )

        results.append({
            "host": host,
            "incident_count": len(incidents),
            "severity": severity
        })

        host_frequency[host] = len(incidents)

    metrics = generate_metrics(results)

    chart_labels = list(host_frequency.keys())

    chart_values = list(host_frequency.values())

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "metrics": metrics,
            "hosts": results,
            "chart_labels": chart_labels,
            "chart_values": chart_values
        }
    )


@app.get("/analyze", response_model=IncidentResponse)
async def analyze(background_tasks: BackgroundTasks):

    start = time.time()
    logs = load_logs()
    logs = logs[:2]
    
    import uuid

    incident_id = str(uuid.uuid4())
    add_to_queue({"incident_id": incident_id, "status": "queued"})
    result = await process_incident(logs)
    background_tasks.add_task(
        save_incident,
        logs,
        result["severity"],
        result["analysis"],
        incident_id
    )

    duration = time.time() - start
    return {
        "incident_id": incident_id,
        "response_time": duration,
        **result
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

@app.get("/analyze/batch")
async def analyze_batch():

    logs = load_logs()

    parsed_logs = parse_logs(logs)

    grouped = group_incidents(parsed_logs)

    results = []

    for host, incidents in grouped.items():

        incident_logs = [
            incident["raw"]
            for incident in incidents
        ]

        result = await process_incident(incident_logs)
        results.append({
            "host": host,
            "incident_count": len(incidents),
            **result
        })
    metrics = generate_metrics(results)
    return {
        "total_hosts": len(results),
        "metrics": metrics,
        "results": results
    }

@app.get("/dashboard")
async def dashboard():

    logs = load_logs()

    parsed_logs = parse_logs(logs)

    grouped = group_incidents(parsed_logs)

    results = []
    host_frequency = {}

    for host, incidents in grouped.items():

        incident_logs = [
            incident["raw"]
            for incident in incidents
        ]
        host_frequency[host] = len(incidents)

        severity = classify_severity(
            incident_logs
        )

        results.append({
            "host": host,
            "incident_count": len(incidents),
            "severity": severity
        })

    metrics = generate_metrics(results)

    trends = analyze_trends(results)

    return {
        "total_hosts": len(results),
        "host_frequency": host_frequency,
        "metrics": metrics,
        "trends": trends,
        "hosts": results
    }

@app.get("/host/{host}")
async def host_details(host: str):
    logs = load_logs()

    parsed_logs = parse_logs(logs)

    host_logs = []

    for incident in parsed_logs:

        if incident["host"] == host:
            host_logs.append(incident)

    return {
        "host": host,
        "incidents": host_logs
    }

@app.get("/queue")
def queue_status():

    return {
        "queue": get_queue()
    }

@app.get("/incident/{incident_id}")
def incident_status(incident_id: str):

    incidents = get_incidents()["incidents"]

    for incident in incidents:

        if incident[0] == incident_id:

            return {
                "id": incident[0],
                "severity": incident[1]
            }

    return {
        "error": "Incident not found"
    }