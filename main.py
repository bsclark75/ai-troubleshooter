from fastapi import FastAPI, BackgroundTasks, Request, UploadFile, File
from fastapi.responses import JSONResponse, HTMLResponse
from app.services.log_service import get_parsed_log_context, is_repeat_notification, build_log_context
from app.services.db_service import init_db, get_incidents, get_incident, get_incident_counts, get_incidents_by_host
from app.services.metrics_service import generate_metrics
from app.services.trend_service import analyze_trends
from app.services.severity_service import get_worst_severity
from fastapi.templating import Jinja2Templates
from app.core.logging_config import logger
from dotenv import load_dotenv
import asyncio
from contextlib import asynccontextmanager
from app.services.worker_service import queue_worker
from typing import List
from log_watcher import watch_logs
from app.services.ingestion_service import process_batch_log
from collections import defaultdict
from datetime import datetime, timedelta



def success_response(data: dict) -> dict:
    return {"success": True, "data": data, "error": None}


def error_response(code: str, message: str) -> dict:
    return {"success": False, "data": None, "error": {"code": code, "message": message}}


@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(queue_worker())
    asyncio.create_task(watch_logs())
    yield

load_dotenv()
app = FastAPI(lifespan=lifespan)
init_db()
#recovered = recover_processing_incidents()

#logger.info(f"Recovered {recovered} interrupted incidents")
templates = Jinja2Templates(directory="templates")
#semaphore = asyncio.Semaphore(3)


def get_incident_trend():
    incidents = get_incidents()

    now = datetime.now()
    start_time = now - timedelta(hours=24)

    buckets = defaultdict(int)

    # Create empty buckets so missing hours show as 0
    for i in range(24):
        hour = (start_time + timedelta(hours=i)).replace(
            minute=0,
            second=0,
            microsecond=0
        )
        buckets[hour] = 0

    for incident in incidents:
        try:
            created = datetime.fromisoformat(incident["opened_at"])

            if created >= start_time:
                bucket = created.replace(
                    minute=0,
                    second=0,
                    microsecond=0
                )
                buckets[bucket] += 1

        except Exception:
            continue

    labels = [
        dt.strftime("%m-%d %H:00")
        for dt in buckets.keys()
        ]

    counts = list(buckets.values())

    return {
        "labels": labels,
        "counts": counts
    }

@app.get("/")
async def dashboard_ui(request: Request):
    incidents = get_incidents()
    groups = {}

    for incident in incidents:
        #print(incident)
        key = (incident["host"], incident["service"])

        if key not in groups:
            groups[key] = {
                "host": incident["host"],
                "service": incident["service"],
                "incident_count": 0,
                "severity": incident["severity"]
            }

        groups[key]["incident_count"] += 1
        groups[key]["severity"] = incident["severity"]

    host_services = sorted(
        groups.values(),
        key=lambda x: (x["host"], x["service"])
    )
    
    metrics = generate_metrics(host_services)
    trend = get_incident_trend()

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "metrics": metrics,
            "host_services": host_services,
            "trend": trend
        }
    )

@app.get("/analyze")
async def analyze():
    context = get_parsed_log_context()
    logs = context["parsed_logs"]
    if not is_repeat_notification(logs[0]):
        #incident_id = create_incident(logs[0])
        pass
    return success_response({
        #"incident_id": incident_id,
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

@app.post("/analyze/batch")
async def analyze_batch(content):
    return await process_batch_log(content)

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
    #incidents = get_incidents_by_host(host)

    if not incidents:
        return JSONResponse(
            status_code=404,
            content=error_response("NOT_FOUND", f"Host '{host}' not found")
        )

    return success_response({
        "host": host,
        "incidents": incidents
    })

"""@app.get("/queue")
def queue_status():
    #queued = get_queued_incidents()

    return success_response({
        #"queued_count": len(queued),
        #"incidents": queued
    })"""


@app.get("/incident/{incident_id}")
def incident_status(incident_id: str):
    incident = get_incident(incident_id)

    if incident:
        return success_response(incident)

    return JSONResponse(
        status_code=404,
        content=error_response("NOT_FOUND", f"Incident '{incident_id}' not found")
    )

"""@app.get("/processing")
def processing():
    #processes = get_processing_incidents()

    return success_response({
        #"processes_count": len(processes),
        #"incidents": processes
    })


@app.get("/failures")
def failures():
    #failures = get_failure_incidents()

    return success_response({
        "failures_count": len(failures),
        "incidents": failures
    })"""


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
    #print(f"host_ui: Incident(s): {incidents}")

    return templates.TemplateResponse(
        request=request,
        name="host.html",
        context={
            "host": host,
            "incidents": incidents,
            "metrics": metrics,
            "trends": trends,
            "incident_count": len(incidents),
            "service": incidents[0]["service"]
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

@app.get("/upload")
async def upload_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="upload_logs.html"
    )


@app.post("/upload", response_class=HTMLResponse)
async def upload_logs(
    request: Request,
    logfile: UploadFile = File(...)
):
 
    try:

        content = await logfile.read()
        lines = content.decode().splitlines()

        result = await process_batch_log(lines)

        return templates.TemplateResponse(
            request=request,
            name="upload_results.html",
            context={
                "result": result
            }
)
    except Exception as e:
        return templates.TemplateResponse(
            request=request,
            name="upload_logs.html",
                context={
                    "error": str(e)
                }
)