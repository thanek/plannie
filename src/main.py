import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from src.api.dependencies import get_session_service
from src.api.routes import router
from src.config import settings


load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(_periodic_purge())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


async def _periodic_purge():
    service = get_session_service()
    while True:
        await asyncio.sleep(settings.PURGE_INTERVAL_SECONDS)
        service.purge_expired_sessions()


app = FastAPI(title="Planning Estimator", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="web/static"), name="static")
app.include_router(router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        timeout_graceful_shutdown=3,
    )

