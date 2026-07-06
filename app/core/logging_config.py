import logging
from logging.handlers import TimedRotatingFileHandler

logger = logging.getLogger("ai_troubleshooter")
logger.setLevel(logging.INFO)

formatter = logging.Formatter(
    "%(asctime)s %(levelname)s %(name)s %(message)s"
)

file_handler = TimedRotatingFileHandler(
    "data/ai_troubleshooter.log",
    when="W0",
    interval=1,
    backupCount=8,
    encoding="utf-8"
)
file_handler.setFormatter(formatter)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

logger.handlers.clear()      # Prevent duplicate handlers if reloaded
logger.addHandler(file_handler)
logger.addHandler(console_handler)
logger.propagate = False