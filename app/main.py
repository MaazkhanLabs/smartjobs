import asyncio
import threading
from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, HTTPException, Request
from fastapi.exception_handlers import http_exception_handler as default_http_exception_handler
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import Base, engine, SessionLocal
from app.models import Job
from app.routers import admin, auth, jobs, profile, survey, web
from app.scrapers.runner import run_company_scraper
from app.scrapers.real_jobs import fetch_and_store_real_jobs


scheduler = BackgroundScheduler()


def run_real_jobs_sync():
    asyncio.run(fetch_and_store_real_jobs())


@asynccontextmanager
async def lifespan(app: FastAPI):
    # For a student project, create tables automatically.
    Base.metadata.create_all(bind=engine)

    if settings.enable_scheduler:
        scheduler.add_job(
            run_company_scraper,
            "interval",
            hours=4,
            id="company_scraper",
            replace_existing=True,
        )
        scheduler.add_job(
            run_real_jobs_sync,
            "interval",
            hours=2,
            id="real_jobs_scraper",
            replace_existing=True,
        )
        scheduler.start()

    # Initial automatic fetch if jobs database is light
    db = SessionLocal()
    try:
        count = db.query(Job).count()
        if count < 10:
            asyncio.create_task(fetch_and_store_real_jobs())
    finally:
        db.close()

    # Optional Telegram process.
    if settings.enable_telegram_bot and settings.telegram_bot_token:
        from app.telegram.bot import run_bot

        thread = threading.Thread(
            target=run_bot,
            daemon=True,
        )
        thread.start()

    yield

    if scheduler.running:
        scheduler.shutdown()


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    lifespan=lifespan,
)


@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 401 and "text/html" in request.headers.get("accept", ""):
        return RedirectResponse("/login")
    return await default_http_exception_handler(request, exc)


app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static",
)

app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(jobs.router)
app.include_router(admin.router)
app.include_router(survey.router)
app.include_router(web.router)


@app.get("/health")
def health():
    return {"status": "ok"}
