from fastapi import FastAPI
from app.services.db_service import init_db
from dotenv import load_dotenv
import asyncio
from contextlib import asynccontextmanager
from app.services.worker_service import queue_worker
from log_watcher import watch_logs
from app.routers.api import api_router
from app.routers.ui import ui_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(queue_worker())
    asyncio.create_task(watch_logs())
    yield

load_dotenv()
app = FastAPI(lifespan=lifespan)
app.include_router(api_router)
app.include_router(ui_router)

init_db()
   
