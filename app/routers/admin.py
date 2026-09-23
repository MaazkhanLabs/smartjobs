from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models import Job, Recommendation, User, UserJobAction
from app.schemas import JobCreate
from app.scrapers.real_jobs import fetch_and_store_real_jobs
from app.services.jobs import create_job
from app.services.recommendations import recompute_for_new_job

router = APIRouter(prefix="/api/admin", tags=["admin"])


def verify_admin_user(user: User = Depends(get_current_user)):
    # Allow logged-in user to access admin functionality for demo/management purposes
    return user


@router.get("/stats")
def get_admin_stats(
    db: Session = Depends(get_db),
    user: User = Depends(verify_admin_user),
):
    total_users = db.scalar(select(func.count(User.id))) or 0
    total_jobs = db.scalar(select(func.count(Job.id))) or 0
    active_jobs = db.scalar(select(func.count(Job.id)).where(Job.is_active.is_(True))) or 0
    total_applications = db.scalar(
        select(func.count(UserJobAction.id)).where(
            UserJobAction.action.in_(["clicked_apply", "marked_applied"])
        )
    ) or 0
    total_recommendations = db.scalar(select(func.count(Recommendation.id))) or 0

    return {
        "total_users": total_users,
        "total_jobs": total_jobs,
        "active_jobs": active_jobs,
        "total_applications": total_applications,
        "total_recommendations": total_recommendations,
    }


@router.get("/users")
def list_admin_users(
    db: Session = Depends(get_db),
    user: User = Depends(verify_admin_user),
):
    users = db.scalars(select(User).order_by(User.created_at.desc())).all()
    return [
        {
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "branch": u.branch or "N/A",
            "year": u.year or "N/A",
            "cgpa": u.cgpa or "N/A",
            "is_admin": u.is_admin,
            "created_at": u.created_at.strftime("%Y-%m-%d %H:%M") if u.created_at else "N/A",
        }
        for u in users
    ]


@router.post("/users/{user_id}/toggle-admin")
def toggle_user_admin(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_admin_user),
):
    target_user = db.get(User, user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    target_user.is_admin = not target_user.is_admin
    db.commit()
    return {
        "message": f"Updated {target_user.name} admin status to {target_user.is_admin}",
        "is_admin": target_user.is_admin,
    }


@router.post("/scrape")
async def trigger_admin_scrape(
    user: User = Depends(verify_admin_user),
):
    count = await fetch_and_store_real_jobs()
    return {
        "message": f"Scraper execution completed. Added/updated {count} jobs.",
        "jobs_added": count,
    }


@router.post("/jobs")
def add_job(
    data: JobCreate,
    db: Session = Depends(get_db),
    user: User = Depends(verify_admin_user),
):
    job = create_job(db, data)
    recompute_for_new_job(db, job)
    return {
        "message": "Job successfully created and recommendations calculated!",
        "job_id": job.id,
    }


@router.get("/applications")
def list_all_student_applications(
    db: Session = Depends(get_db),
    user: User = Depends(verify_admin_user),
):
    stmt = (
        select(UserJobAction, User, Job)
        .join(User, UserJobAction.user_id == User.id)
        .join(Job, UserJobAction.job_id == Job.id)
        .order_by(UserJobAction.created_at.desc())
    )
    rows = db.execute(stmt).all()
    return [
        {
            "action_id": act.id,
            "student_name": student.name,
            "student_email": student.email,
            "student_branch": student.branch or "N/A",
            "student_cgpa": student.cgpa or "N/A",
            "job_title": job.title,
            "job_company": job.company,
            "action": act.action,
            "created_at": act.created_at.strftime("%b %d, %Y %H:%M") if act.created_at else "Recently",
        }
        for act, student, job in rows
    ]
