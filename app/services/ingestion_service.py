from app.core.config import semaphore
from app.core.logging_config import logger
from app.services.log_service import (
    is_repeat_notification,
    process_event,
    build_log_context
)
import asyncio

async def process_host(host, incidents):
    async with semaphore:
        logger.info(f"Worker started for {host}")
        incident_ids = []
        for incident in incidents:
            #print(f"Working on {incident}")
            if is_repeat_notification(incident):
                print("Skipping")
                continue
            new_id = process_event(incident)
            print(f"New id: {new_id}")
            incident_ids.append(new_id)

        logger.info(f"Worker completed for {host}")

        return {
            "host": host,
            "incident_count": len(incidents),
            "incident_ids": incident_ids
        }
    
async def process_batch_log(content: str):
    context = build_log_context(content)
    #print(f"ingestion_service state of context: {context}")
    tasks = [
        process_host(host, incidents)
        for host, incidents in context["grouped"].items()
    ]

    results = await asyncio.gather(*tasks)
