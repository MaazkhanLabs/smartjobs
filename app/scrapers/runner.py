import asyncio

from app.database import SessionLocal
from app.scrapers.dummy_company import scrape_dummy_company
from app.services.jobs import create_job
from app.services.recommendations import recompute_for_new_job


async def run_company_scraper():
    jobs = await scrape_dummy_company()

    db = SessionLocal()

    try:
        for data in jobs:
            job = create_job(db, data)
            recompute_for_new_job(db, job)
    finally:
        db.close()


def run_company_scraper_sync():
    asyncio.run(run_company_scraper())


def run_email_import(email_text: str):
    from app.scrapers.email_parser import parse_college_email

    data = parse_college_email(email_text)

    db = SessionLocal()

    try:
        job = create_job(db, data)
        recompute_for_new_job(db, job)
    finally:
        db.close()
