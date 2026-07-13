from app.services.db_service import (
    get_incidents, 
    get_incident,
    get_incident_counts,
    update_incident,
    get_incidents_by_host,
)
from app.services.ingestion_service import process_batch_log
from app.services.severity_service import get_worst_severity
from app.services.metrics_service import generate_metrics
from app.services.trend_service import analyze_trends
from fastapi.responses import JSONResponse
from app.core.logging_config import logger
from fastapi import APIRouter, Body
from app.services.incident_processor import process_incident
from app.utils.responses import success_response, error_response
from app.models.api_models import APIResponse
from typing import List

api_router = APIRouter(
    prefix="/api",
    tags=["API"]
)

@api_router.get(
    "/incidents",
    response_model=APIResponse
)
def list_incidents():
    return success_response({
        "incidents": get_incidents()
    })

@api_router.get(
    "/health",
    response_model=APIResponse
)
def health():
    return success_response({
        "status": "healthy"
    })

@api_router.post(
    "/analyze/batch",
    response_model=APIResponse
)
async def analyze_batch(
    content: List[str] = Body(...)
):
    result = await process_batch_log(content)

    return success_response(result)

@api_router.get(
    "/dashboard",
    response_model=APIResponse
)
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

@api_router.get(
    "/host/{host}",
    response_model=APIResponse
)
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

"""@api_router.get("/queue")
def queue_status():
    #queued = get_queued_incidents()

    return success_response({
        #"queued_count": len(queued),
        #"incidents": queued
    })"""


@api_router.get(
    "/incident/{incident_id}",
    response_model=APIResponse
)
def incident_details(incident_id: str):
    incident = get_incident(incident_id)

    if incident:
        return success_response(incident)

    return JSONResponse(
        status_code=404,
        content=error_response("NOT_FOUND", f"Incident '{incident_id}' not found")
    )

"""@api_router.get("/processing")
def processing():
    #processes = get_processing_incidents()

    return success_response({
        #"processes_count": len(processes),
        #"incidents": processes
    })


@api_router.get("/failures")
def failures():
    #failures = get_failure_incidents()

    return success_response({
        "failures_count": len(failures),
        "incidents": failures
    })"""


@api_router.get(
    "/stats",
    response_model=APIResponse
)
def stats():
    groups = get_incident_counts()

    return success_response({
        "queued": groups["queued"],
        "processing": groups["processing"],
        "completed": groups["completed"],
        "failed": groups["failed"]
    })

@api_router.post(
    "/incident/{incident_id}/analyze",
    response_model=APIResponse
)
async def analyze(incident_id):
    try:

        logger.info("analysis request recieved")
        incident = get_incident(incident_id)
        if incident is None:
            return JSONResponse(
                status_code=404,
                content=error_response(
                    "NOT_FOUND",
                    "Incident not found"
                )
            )
        result = await process_incident(incident)
        logger.info("Ai return results")

        update_incident(
            incident["incident_id"],
            result["severity"],
            result["analysis"],
            "open"
        )
        logger.info("Database updated")
        
        return success_response({
            "severity": result["severity"],
            "analysis": result["analysis"]
        })
    
    except Exception as ex:
        logger.exception(
            "Failed to analyze incident %s",
            incident_id
        )

        return JSONResponse(
            status_code=500,
            content=error_response(
                "ANALYSIS_FAILED",
                str(ex)
            )
        )
