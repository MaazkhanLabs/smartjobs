from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Job, JobSkill


def create_job(db: Session, data):
    if data.external_id:
        existing = db.scalar(
            select(Job).where(
                Job.source == data.source,
                Job.external_id == data.external_id,
            )
        )
        if existing:
            return existing

    job = Job(
        title=data.title,
        company=data.company,
        description=data.description,
        location=data.location,
        work_mode=data.work_mode,
        role_type=data.role_type,
        compensation=data.compensation,
        compensation_period=data.compensation_period,
        min_cgpa=data.min_cgpa,
        eligible_branches=",".join(data.eligible_branches),
        eligible_years=",".join(map(str, data.eligible_years)),
        apply_url=data.apply_url,
        source=data.source,
        external_id=data.external_id,
    )

    db.add(job)
    db.flush()

    for skill in data.skills:
        normalized = skill.strip().lower()
        if normalized:
            db.add(JobSkill(job_id=job.id, skill=normalized))

    db.commit()
    db.refresh(job)

    return job
