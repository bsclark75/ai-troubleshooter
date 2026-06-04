import asyncio
import logging
from app.services.incident_processor import process_incident
from app.services.db_service import get_next_queued_incident,update_incident_status, update_incident, increment_retry_count, get_retry_count
from app.core.config import MAX_RETRIES

logger = logging.getLogger(__name__)

async def queue_worker():

    logger.info("Queue worker started")

    while True:

        incident = get_next_queued_incident()

        if incident:

            logger.info(
                f"Processing queued incident "
                f"{incident['incident_id']}"
            )

            try:

                update_incident_status(incident['incident_id'], "processing")
                
                #print(f"I am going to try to process this: {incident['logs']}")
                result = await process_incident(
                    incident["logs"]
                )

                update_incident(
                    incident["incident_id"],
                    result["severity"],
                    result["analysis"],
                    "completed"
                )


                logger.info(
                    f"Completed incident "
                    f"{incident['incident_id']}"
                )

            except Exception as e:

                increment_retry_count(incident["incident_id"])
                retry_count = get_retry_count(incident["incident_id"])

                if retry_count < MAX_RETRIES:

                    delay = 10 * retry_count

                    update_incident_status(
                        incident["incident_id"],
                        "queued", delay
                        )

                    logger.exception(
                        f"Retrying incident "
                        f"{incident['incident_id']}"
                        )

                else:

                    update_incident_status(
                    incident["incident_id"],
                        "failed"
                        )

                    logger.error(
                        f"Incident permanently failed "
                        f"{incident['incident_id']}"
                        )

        await asyncio.sleep(1)

