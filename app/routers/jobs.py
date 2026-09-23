from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Job, Recommendation, User, UserJobAction
from app.schemas import ActionCreate
from app.scrapers.real_jobs import fetch_and_store_real_jobs, search_live_jobs_on_demand

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.post("/fetch-real-jobs")
async def trigger_fetch_real_jobs(user: User = Depends(get_current_user)):
    count = await fetch_and_store_real_jobs()
    return {
        "message": f"Successfully fetched and processed {count} live real-time job listings!",
        "count": count,
    }


@router.get("/analytics")
def get_job_market_analytics(db: Session = Depends(get_db)):
    jobs = db.scalars(select(Job).where(Job.is_active.is_(True))).all()

    total_jobs = len(jobs)
    platform_counts: dict[str, int] = {}
    work_mode_counts: dict[str, int] = {}
    role_type_counts: dict[str, int] = {}
    skill_counts: dict[str, int] = {}

    for job in jobs:
        src = (job.source or "Direct").lower()
        platform_counts[src] = platform_counts.get(src, 0) + 1

        wm = (job.work_mode or "onsite").lower()
        work_mode_counts[wm] = work_mode_counts.get(wm, 0) + 1

        rt = (job.role_type or "internship").lower()
        role_type_counts[rt] = role_type_counts.get(rt, 0) + 1

        for s_obj in job.skills:
            s_name = s_obj.skill.strip().title()
            skill_counts[s_name] = skill_counts.get(s_name, 0) + 1

    top_skills = sorted(
        [{"skill": k, "count": v} for k, v in skill_counts.items()],
        key=lambda x: x["count"],
        reverse=True,
    )[:10]

    return {
        "total_jobs": total_jobs,
        "platforms": platform_counts,
        "work_modes": work_mode_counts,
        "role_types": role_type_counts,
        "top_skills": top_skills,
    }



@router.get("")
async def list_jobs(
    search: str | None = None,
    location: str | None = None,
    work_mode: str | None = None,
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db),
):
    if search and len(search.strip()) >= 2:
        try:
            await search_live_jobs_on_demand(search.strip())
        except Exception as exc:
            print(f"On-demand live search error: {exc}")

    stmt = select(Job).where(Job.is_active.is_(True))

    if search:
        pattern = f"%{search.lower()}%"
        stmt = stmt.where(
            Job.title.ilike(pattern)
            | Job.company.ilike(pattern)
            | Job.description.ilike(pattern)
        )

    if location:
        stmt = stmt.where(Job.location.ilike(f"%{location}%"))

    if work_mode:
        stmt = stmt.where(Job.work_mode == work_mode.lower())

    jobs = db.scalars(
        stmt.order_by(Job.posted_at.desc()).limit(limit)
    ).all()

    return jobs


@router.get("/recommended")
async def recommended_jobs(
    search: str | None = None,
    location: str | None = None,
    work_mode: str | None = None,
    min_score: float = Query(default=0, ge=0, le=1),
    limit: int = Query(default=50, le=200),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if search and len(search.strip()) >= 2:
        try:
            await search_live_jobs_on_demand(search.strip())
        except Exception as exc:
            print(f"On-demand live search error: {exc}")

    stmt = (
        select(Recommendation, Job)
        .join(Job, Recommendation.job_id == Job.id)
        .where(
            Recommendation.user_id == user.id,
            Recommendation.score >= min_score,
            Job.is_active.is_(True),
        )
    )

    if search:
        pattern = f"%{search.lower()}%"
        stmt = stmt.where(
            Job.title.ilike(pattern)
            | Job.company.ilike(pattern)
            | Job.description.ilike(pattern)
        )

    if location:
        stmt = stmt.where(Job.location.ilike(f"%{location}%"))

    if work_mode:
        stmt = stmt.where(Job.work_mode == work_mode.lower())

    rows = db.execute(
        stmt.order_by(Recommendation.score.desc()).limit(limit)
    ).all()

    return [
        {
            "id": job.id,
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "work_mode": job.work_mode,
            "role_type": job.role_type,
            "compensation": job.compensation,
            "compensation_period": job.compensation_period,
            "apply_url": job.apply_url,
            "source": job.source,
            "score": round(rec.score, 3),
            "explanation": rec.explanation,
        }
        for rec, job in rows
    ]


@router.get("/my-applications")
def get_my_applications(
    filter_type: str | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stmt = (
        select(UserJobAction, Job)
        .join(Job, UserJobAction.job_id == Job.id)
        .where(UserJobAction.user_id == user.id)
    )
    if filter_type == "applied":
        stmt = stmt.where(
            UserJobAction.action.in_(
                ["clicked_apply", "marked_applied", "interviewing", "offered", "rejected"]
            )
        )
    elif filter_type == "saved":
        stmt = stmt.where(UserJobAction.action == "saved")
    else:
        stmt = stmt.where(
            UserJobAction.action.in_(
                ["clicked_apply", "marked_applied", "saved", "interviewing", "offered", "rejected"]
            )
        )

    rows = db.execute(stmt.order_by(UserJobAction.created_at.desc())).all()

    latest_by_job = {}
    for act, job in rows:
        if job.id not in latest_by_job:
            latest_by_job[job.id] = {
                "action_id": act.id,
                "action": act.action,
                "created_at": act.created_at.strftime("%b %d, %Y %H:%M") if act.created_at else "Recently",
                "job": {
                    "id": job.id,
                    "title": job.title,
                    "company": job.company,
                    "location": job.location,
                    "work_mode": job.work_mode,
                    "role_type": job.role_type,
                    "compensation": job.compensation,
                    "compensation_period": job.compensation_period,
                    "apply_url": job.apply_url,
                    "source": job.source,
                },
            }

    return list(latest_by_job.values())


from app.matching import get_skill_gap_analysis
from app.services.interview_prep import generate_interview_prep


@router.get("/{job_id}")
def get_job(
    job_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = db.get(Job, job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    recommendation = db.scalar(
        select(Recommendation).where(
            Recommendation.user_id == user.id,
            Recommendation.job_id == job.id,
        )
    )

    skill_gap = get_skill_gap_analysis(user, job)
    job_skills_list = [s.skill for s in job.skills]
    interview_prep = generate_interview_prep(job_skills_list)

    return {
        "job": job,
        "recommendation": {
            "score": recommendation.score,
            "explanation": recommendation.explanation,
        } if recommendation else None,
        "skill_gap": skill_gap,
        "interview_prep": interview_prep,
    }



@router.post("/{job_id}/action")
def mark_action(
    job_id: int,
    data: ActionCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    allowed = {
        "viewed",
        "clicked_apply",
        "marked_applied",
        "not_interested",
        "saved",
        "interviewing",
        "offered",
        "rejected",
    }

    if data.action not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Action must be one of: {', '.join(sorted(allowed))}",
        )

    db.add(
        UserJobAction(
            user_id=user.id,
            job_id=job_id,
            action=data.action,
        )
    )
    db.commit()

    return {"message": "Action recorded"}


from app.services.ai_tools import generate_cold_email_and_cover_letter


@router.post("/{job_id}/generate-outreach")
def generate_outreach(
    job_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    outreach = generate_cold_email_and_cover_letter(user, job)
    return outreach


