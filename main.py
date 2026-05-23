from fastapi import FastAPI, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from app.services.log_service import get_parsed_log_context, create_incident
from app.services.severity_service import classify_severity
from app.services.db_service import *
from app.services.metrics_service import generate_metrics
from app.services.trend_service import analyze_trends
from fastapi.templating import Jinja2Templates
from app.core.logging_config import logger
from dotenv import load_dotenv
import asyncio
from contextlib import asynccontextmanager
from app.services.worker_service import queue_worker


def success_response(data: dict) -> dict:
    return {"success": True, "data": data, "error": None}


def error_response(code: str, message: str) -> dict:
    return {"success": False, "data": None, "error": {"code": code, "message": message}}


@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(queue_worker())
    yield


load_dotenv()
app = FastAPI(lifespan=lifespan)
init_db()
recovered = recover_processing_incidents()

logger.info(f"Recovered {recovered} interrupted incidents")
templates = Jinja2Templates(directory="templates")
semaphore = asyncio.Semaphore(3)


@app.get("/")
async def dashboard_ui(request: Request):
    context = get_parsed_log_context()

    results = []
    host_frequency = {}

    for host, incidents in context["grouped"].items():
        severity = classify_severity([incident["raw"] for incident in incidents])
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
    context = get_parsed_log_context()
    logs = context["logs"][:2]
    incident_id = create_incident(logs)

    return success_response({
        "incident_id": incident_id,
        "status": "queued"
    })


@app.get("/incidents")
def incidents():
    return success_response({
        "incidents": get_incidents()
    })


@app.get("/health")
def health():
    return success_response({
        "status": "healthy"
    })


@app.get("/analyze/batch")
async def analyze_batch():
    context = get_parsed_log_context()

    tasks = [
        process_host(host, incidents)
        for host, incidents in context["grouped"].items()
    ]

    results = await asyncio.gather(*tasks)

    return success_response({
        "total_hosts": len(results),
        "results": results
    })


@app.get("/dashboard")
async def dashboard():
    context = get_parsed_log_context()

    results = []
    host_frequency = {}

    for host, incidents in context["grouped"].items():
        incident_logs = [incident["raw"] for incident in incidents]
        host_frequency[host] = len(incidents)
        severity = classify_severity(incident_logs)
        results.append({
            "host": host,
            "incident_count": len(incidents),
            "severity": severity
        })

    metrics = generate_metrics(results)
    trends = analyze_trends(results)

    return success_response({
        "total_hosts": len(results),
        "host_frequency": host_frequency,
        "metrics": metrics,
        "trends": trends,
        "hosts": results
    })


@app.get("/host/{host}")
async def host_details(host: str):
    context = get_parsed_log_context()

    host_logs = [
        incident for incident in context["parsed_logs"]
        if incident["host"] == host
    ]

    return success_response({
        "host": host,
        "incidents": host_logs
    })


@app.get("/queue")
def queue_status():
    queued = get_queued_incidents()

    return success_response({
        "queued_count": len(queued),
        "incidents": queued
    })


@app.get("/incident/{incident_id}")
def incident_status(incident_id: str):
    incident = get_incident(incident_id)

    if incident:
        return success_response(incident)

    return JSONResponse(
        status_code=404,
        content=error_response("NOT_FOUND", f"Incident '{incident_id}' not found")
    )


async def process_host(host, incidents):
    async with semaphore:
        logger.info(f"Worker started for {host}")

        incident_ids = []
        for incident in incidents:
            new_id = create_incident(incident)
            incident_ids.append(new_id)

        logger.info(f"Worker completed for {host}")

        return {
            "host": host,
            "incident_count": len(incidents),
            "incident_ids": incident_ids
        }


@app.get("/processing")
def processing():
    processes = get_processing_incidents()

    return success_response({
        "processes_count": len(processes),
        "incidents": processes
    })


@app.get("/failures")
def failures():
    failures = get_failure_incidents()

    return success_response({
        "failures_count": len(failures),
        "incidents": failures
    })


@app.get("/stats")
def stats():
    groups = get_incident_counts()

    return success_response({
        "queued": groups["queued"],
        "processing": groups["processing"],
        "completed": groups["completed"],
        "failed": groups["failed"]
    })