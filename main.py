from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI
from app.services.db_service import init_db
import asyncio
from contextlib import asynccontextmanager
from app.services.worker_service import queue_worker
from log_watcher import watch_logs
from app.routers.api import api_router
from app.routers.ui import ui_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    asyncio.create_task(queue_worker())
    asyncio.create_task(watch_logs())
    yield

app = FastAPI(lifespan=lifespan)
app.include_router(api_router)
app.include_router(ui_router)

   
