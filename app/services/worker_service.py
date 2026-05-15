import asyncio
import logging
from app.services.queue_service import pop_queue
from app.services.incident_processor import process_incident
from app.services.db_service import save_incident

logger = logging.getLogger(__name__)

async def queue_worker():

    logger.info("Queue worker started")

    while True:

        incident = pop_queue()

        if incident:

            logger.info(
                f"Processing queued incident "
                f"{incident['incident_id']}"
            )

            try:

                incident["status"] = "processing"

                result = await process_incident(
                    incident["logs"]
                )

                incident["result"] = result
                save_incident(
                   incident["logs"],
                    result["severity"],
                    result["analysis"],
                    incident["incident_id"]
                )

                incident["status"] = "completed"

                logger.info(
                    f"Completed incident "
                    f"{incident['incident_id']}"
                )

            except Exception as e:

                incident["status"] = "failed"

                incident["error"] = str(e)

                logger.error(str(e))

        await asyncio.sleep(1)