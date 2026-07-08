from fastapi import APIRouter, Request, UploadFile, File
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from app.services.db_service import (
    get_incidents,
    get_incidents_by_host,
    get_incident,
)
from app.services.metrics_service import generate_metrics
from app.services.trend_service import analyze_trends
from app.services.ingestion_service import process_batch_log
from app.utils.responses import error_response
from app.services.trend_service import get_incident_trend

ui_router = APIRouter()
templates = Jinja2Templates(directory="templates")

@ui_router.get("/")
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

@ui_router.get("/host/{host}/ui")
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

@ui_router.get("/incident/{incident_id}/ui")
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

@ui_router.post("/upload", response_class=HTMLResponse)
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
