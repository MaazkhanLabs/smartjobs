from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.matching import calculate_match
from app.models import Job, Recommendation, User


def recompute_for_user(db: Session, user: User):
    jobs = db.scalars(
        select(Job).where(Job.is_active.is_(True))
    ).all()

    for job in jobs:
        score, explanation = calculate_match(user, job)

        existing = db.scalar(
            select(Recommendation).where(
                Recommendation.user_id == user.id,
                Recommendation.job_id == job.id,
            )
        )

        if score <= 0:
            if existing:
                db.delete(existing)
            continue

        if existing:
            existing.score = score
            existing.explanation = explanation
        else:
            db.add(
                Recommendation(
                    user_id=user.id,
                    job_id=job.id,
                    score=score,
                    explanation=explanation,
                )
            )

    db.commit()


def recompute_for_all_users(db: Session):
    users = db.scalars(select(User)).all()

    for user in users:
        recompute_for_user(db, user)


def recompute_for_new_job(db: Session, job: Job):
    users = db.scalars(select(User)).all()

    for user in users:
        score, explanation = calculate_match(user, job)

        if score <= 0:
            continue

        existing = db.scalar(
            select(Recommendation).where(
                Recommendation.user_id == user.id,
                Recommendation.job_id == job.id,
            )
        )

        if existing:
            existing.score = score
            existing.explanation = explanation
        else:
            db.add(
                Recommendation(
                    user_id=user.id,
                    job_id=job.id,
                    score=score,
                    explanation=explanation,
                )
            )

    db.commit()
