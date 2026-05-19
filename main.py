from fastapi import FastAPI, BackgroundTasks, Request
from app.services.log_service import load_logs
from app.services.severity_service import classify_severity
from app.services.db_service import *
from app.services.log_parser_service import parse_logs, group_incidents
from app.services.metrics_service import generate_metrics
from app.services.trend_service import analyze_trends
from app.services.incident_processor import process_incident
from fastapi.templating import Jinja2Templates
from app.services.queue_service import add_to_queue, get_queue, get_active_incident
from app.core.logging_config import logger
import uuid
from dotenv import load_dotenv
import asyncio
from contextlib import asynccontextmanager
from app.services.worker_service import queue_worker

@asynccontextmanager
async def lifespan(app: FastAPI):

    asyncio.create_task(
        queue_worker()
    )

    yield
    
load_dotenv()
app = FastAPI(lifespan=lifespan)
init_db()
recovered = recover_processing_incidents()

logger.info(
    f"Recovered {recovered} interrupted incidents"
)
templates = Jinja2Templates(directory="templates")
semaphore = asyncio.Semaphore(1)

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


@app.get("/analyze")
async def analyze():

    logs = load_logs()

    logs = logs[:2]

    incident_id = str(uuid.uuid4())

    incident = {
        "incident_id": incident_id,
        "logs": logs,
        "status": "queued"
    }

    save_incident(
        logs,
        "pending",
        {},
        incident_id,
        status="queued"
    )

#    add_to_queue(incident)

    return {
        "incident_id": incident_id,
        "status": "queued"
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

    tasks = [
        process_host(host, incidents)
        for host, incidents in grouped.items()
        ]

    results = await asyncio.gather(*tasks)

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

    queued = get_queued_incidents()

    return {
        "queued_count": len(queued),
        "incidents": queued
    }

@app.get("/incident/{incident_id}")
def incident_status(incident_id: str):

    incident = get_active_incident(
        incident_id
    )

    if incident:

        return incident

    return {
        "error": "Incident not found"
    }
async def process_host(host, incidents):

    async with semaphore:

        logger.info(
            f"Worker started for {host}"
        )

        incident_logs = [
            incident["raw"]
            for incident in incidents
        ]

        result = await process_incident(
            incident_logs
        )

        incident_id = str(uuid.uuid4())
        save_incident(
            incident_logs,
            result["severity"],
            result["analysis"],
            incident_id
        )
        logger.info(
            f"Worker completed for {host}"
        )

        return {
            "host": host,
            "incident_count": len(incidents),
            **result
        }

@app.get("/processing")
def processing():
    
    processes = get_processing_incidents()

    return {
        "processes_count": len(processes),
        "incidents": processes
    }   

@app.get("/failures")
def failures():
    
    failures = get_failure_incidents()

    return {
        "failures_count": len(failures),
        "incidents": failures
    }  

@app.get("/stats")
def stats(): 
    groups = get_incident_counts()
    return{
    "queued": groups["queued"],
    "processing": groups["processing"],
    "completed": groups["completed"],
    "failed": groups["failed"]
}
