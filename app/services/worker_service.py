import asyncio
import logging
from app.services.incident_processor import process_incident
from app.services.db_service import get_next_queued_incident,update_incident_status, update_incident, increment_retry_count, get_retry_count
from app.core.config import MAX_RETRIES

logger = logging.getLogger(__name__)

async def process_next_queued_incident():

    incident = get_next_queued_incident()

    if not incident:
        return False

    update_incident_status(
        incident["incident_id"],
        "processing"
    )

    result = await process_incident(incident)

    update_incident(
        incident["incident_id"],
        result["severity"],
        result["analysis"],
        "completed"
    )

    return True

async def queue_worker():

    logger.info("Queue worker started")

    while True:
        await process_next_queued_incident()
        await asyncio.sleep(1)