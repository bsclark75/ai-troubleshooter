import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    handlers=[
        logging.FileHandler("data/ai_troubleshooter.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("ai_troubleshooter")