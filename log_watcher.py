import os
import json
import asyncio
from app.services.log_service import build_log_context
from app.services.ingestion_service import process_host
from app.core.config import NAGIOSLOGFILE, STATEFILE, ARCHIVE_DIR
from app.core.logging_config import logger

def load_state():
    """
    Returns:
        (inode, offset)
    """

    if not os.path.exists(STATEFILE):
        return None, 0

    try:
        with open(STATEFILE, "r") as f:
            state = json.load(f)

        return (
            state.get("inode"),
            state.get("offset", 0)
        )

    except (json.JSONDecodeError, OSError) as e:
        logger.error("Failed to load state file: %s", e, exc_info=True)
        return None, 0


def save_state(inode, offset):
    """
    Persist current read position.
    """

    state = {
        "inode": inode,
        "offset": offset
    }

    try:
        with open(STATEFILE, "w") as f:
            json.dump(state, f)

    except OSError as e:
        logger.error("Failed to save file: %s",e,exc_info=True)

def check_for_new_lines(saved_inode,saved_offset):
    #logger.info("Checking for new lines")
# 1. Get current file stats
    try:
        current_stat = os.stat(NAGIOSLOGFILE)
        current_inode = current_stat.st_ino
        current_size = current_stat.st_size
    except FileNotFoundError:
        logger.error("Log file not found.")
        current_inode, current_size = None, 0

    if saved_inode is None:
        with open(NAGIOSLOGFILE, "r") as f:
            f.seek(0, os.SEEK_END)
        return [], current_size, current_inode

# 2. Check for log rotation
    if current_inode and current_inode != saved_inode:
        logger.info("Log rotated")

        rotated_path = None

        for fname in os.listdir(ARCHIVE_DIR):
            full_path = os.path.join(ARCHIVE_DIR, fname)

            try:
                if os.stat(full_path).st_ino == saved_inode:
                    rotated_path = full_path
                    break
            except OSError:
                continue
    
        if rotated_path:
            logger.info("Found rotated file: %s", rotated_path)

            with open(rotated_path, "r") as old_file:
                old_file.seek(saved_offset)
                old_lines = old_file.readlines()

            with open(NAGIOSLOGFILE, "r") as new_file:
                new_lines = new_file.readlines()

            all_lines = old_lines + new_lines

            return (
                all_lines,
                os.path.getsize(NAGIOSLOGFILE),
                current_inode
            )
    
    else:
    # No rotation: Use standard offset logic
        #logger.info("Log not rotated.  Reading from saved offset.")
        with open(NAGIOSLOGFILE, "r") as nagios_file:
            if current_size < saved_offset:
                nagios_file.seek(0) # Fallback if file was truncated without inode change
            else:
                nagios_file.seek(saved_offset)
            
            new_lines = nagios_file.readlines()
            new_offset = os.path.getsize(NAGIOSLOGFILE)
            new_saved_inode = saved_inode
        return new_lines, new_offset, new_saved_inode

async def process_lines(processing_lines):

    context = build_log_context(processing_lines)

    tasks = [
        process_host(host, incidents)
        for host, incidents in context["grouped"].items()
    ]

    return await asyncio.gather(*tasks)


async def watch_logs():
    inode, offset = load_state()

    while True:
        lines, new_offset, new_inode = check_for_new_lines(
            inode,
            offset
        )

        if lines:
            logger.info("New lines detected. Processing...")
            results = await process_lines(lines)

            if all(results):
                inode = new_inode
                offset = new_offset
                save_state(inode, offset)

        elif inode is None:
            inode = new_inode
            offset = new_offset
            save_state(inode, offset)

        await asyncio.sleep(60)
