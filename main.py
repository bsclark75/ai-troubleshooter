from fastapi import FastAPI, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from app.services.log_service import get_parsed_log_context, create_incident, is_repeat_notification
from app.services.db_service import *
from app.services.metrics_service import generate_metrics
from app.services.trend_service import analyze_trends
from app.services.severity_service import get_worst_severity
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
    incidents = get_incidents()
    results = []
    host_frequency = {}

    for incident in incidents:
        host = incident["host"]
        host_frequency[host] = host_frequency.get(host, 0) + 1

    for host, count in host_frequency.items():
        host_incidents = [i for i in incidents if i["host"] == host]
        worst_severity = get_worst_severity(host_incidents)
        results.append({
            "host": host,
            "incident_count": count,
            "severity": worst_severity
        })

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
    logs = context["parsed_logs"]
    if not is_repeat_notification(logs[0]):
        incident_id = create_incident(logs[0])

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
    incidents = get_incidents()
    results = []
    host_frequency = {}

    for incident in incidents:
        host = incident["host"]
        host_frequency[host] = host_frequency.get(host, 0) + 1

    for host, count in host_frequency.items():
        host_incidents = [i for i in incidents if i["host"] == host]
        worst_severity = get_worst_severity(host_incidents)
        results.append({
            "host": host,
            "incident_count": count,
            "severity": worst_severity
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
    incidents = get_incidents_by_host(host)

    if not incidents:
        return JSONResponse(
            status_code=404,
            content=error_response("NOT_FOUND", f"Host '{host}' not found")
        )

    return success_response({
        "host": host,
        "incidents": incidents
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
            if is_repeat_notification(incident):
                continue
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

@app.get("/host/{host}/ui")
async def host_ui(host: str, request: Request):
    incidents = get_incidents_by_host(host)

    if not incidents:
        return JSONResponse(
            status_code=404,
            content=error_response("NOT_FOUND", f"Host '{host}' not found")
        )

    metrics = generate_metrics(incidents)
    trends = analyze_trends(incidents)

    return templates.TemplateResponse(
        request=request,
        name="host.html",
        context={
            "host": host,
            "incidents": incidents,
            "metrics": metrics,
            "trends": trends,
            "incident_count": len(incidents)
        }
    )

@app.get("/incident/{incident_id}/ui")
async def incident_ui(incident_id: str, request: Request):
    incident = get_incident(incident_id)

    if not incident:
        return JSONResponse(
            status_code=404,
            content=error_response("NOT_FOUND", f"Incident '{incident_id}' not found")
        )

    return templates.TemplateResponse(
        request=request,
        name="incident.html",
        context={
            "incident": incident
        }
    )