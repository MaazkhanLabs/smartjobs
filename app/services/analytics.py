from datetime import datetime, timedelta, timezone
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Job, Recommendation, User, UserJobAction


def get_analytics(db: Session):
    total_users = db.scalar(
        select(func.count(User.id))
    ) or 0

    total_jobs = db.scalar(
        select(func.count(Job.id))
    ) or 0

    total_recommendations = db.scalar(
        select(func.count(Recommendation.id))
    ) or 0

    average_recommendations_per_user = (
        total_recommendations / total_users
        if total_users
        else 0
    )

    viewed = db.scalar(
        select(func.count(UserJobAction.id)).where(
            UserJobAction.action == "viewed"
        )
    ) or 0

    clicked = db.scalar(
        select(func.count(UserJobAction.id)).where(
            UserJobAction.action == "clicked_apply"
        )
    ) or 0

    applied = db.scalar(
        select(func.count(UserJobAction.id)).where(
            UserJobAction.action == "marked_applied"
        )
    ) or 0

    ctr = clicked / viewed if viewed else 0
    application_rate = applied / viewed if viewed else 0

    return {
        "total_users": total_users,
        "total_jobs": total_jobs,
        "total_recommendations": total_recommendations,
        "average_recommendations_per_user": round(
            average_recommendations_per_user, 2
        ),
        "views": viewed,
        "apply_clicks": clicked,
        "marked_applied": applied,
        "ctr": round(ctr, 4),
        "application_rate": round(application_rate, 4),
    }


def weekly_relevance_stats(db: Session):
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)

    rows = db.execute(
        select(
            UserJobAction.user_id,
            func.count(
                func.distinct(UserJobAction.job_id)
            ).label("relevant_jobs_seen"),
        )
        .where(
            UserJobAction.action == "viewed",
            UserJobAction.created_at >= seven_days_ago,
        )
        .group_by(UserJobAction.user_id)
    ).all()

    return [
        {
            "user_id": user_id,
            "relevant_opportunities_seen": count,
        }
        for user_id, count in rows
    ]
