from fastapi import APIRouter, Depends
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User, UserPreference, UserSkill
from app.schemas import PreferencesUpdate, SkillsUpdate, UserProfileUpdate
from app.services.recommendations import recompute_for_user
from app.telegram.bot import create_link_token

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get("")
def get_profile(user: User = Depends(get_current_user)):
    preferences = user.preferences

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "branch": user.branch,
        "year": user.year,
        "cgpa": user.cgpa,
        "skills": [skill.skill for skill in user.skills],
        "preferences": {
            "roles": preferences.roles.split(",") if preferences and preferences.roles else [],
            "locations": preferences.locations.split(",") if preferences and preferences.locations else [],
            "work_mode": preferences.work_mode if preferences else "any",
            "min_compensation": preferences.min_compensation if preferences else 0,
        },
    }


@router.put("")
def update_profile(
    data: UserProfileUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)

    recompute_for_user(db, user)

    return {"message": "Profile updated"}


@router.put("/skills")
def update_skills(
    data: SkillsUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db.execute(delete(UserSkill).where(UserSkill.user_id == user.id))
    db.flush()

    unique_skills = {skill.strip().lower() for skill in data.skills if skill.strip()}
    for skill in sorted(unique_skills):
        db.add(UserSkill(user_id=user.id, skill=skill))

    db.commit()
    db.refresh(user)

    recompute_for_user(db, user)

    return {"skills": [skill.skill for skill in user.skills]}


@router.put("/preferences")
def update_preferences(
    data: PreferencesUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    preferences = user.preferences

    if not preferences:
        preferences = UserPreference(user_id=user.id)
        db.add(preferences)

    preferences.roles = ",".join(
        item.strip().lower()
        for item in data.roles
        if item.strip()
    )
    preferences.locations = ",".join(
        item.strip().lower()
        for item in data.locations
        if item.strip()
    )
    preferences.work_mode = data.work_mode.lower()
    preferences.min_compensation = data.min_compensation

    db.commit()
    db.refresh(user)

    recompute_for_user(db, user)

    return {"message": "Preferences updated"}


@router.post("/telegram/link-token")
def telegram_link_token(
    user: User = Depends(get_current_user),
):
    token = create_link_token(user.id)

    return {
        "token": token,
        "bot_start_link": (
            f"https://t.me/YOUR_BOT_USERNAME?start={token}"
        ),
        "note": "Replace YOUR_BOT_USERNAME with your Telegram bot username.",
    }


from app.models import JobSkill
from app.services.ai_tools import calculate_ats_score_and_recommendations


@router.get("/ats-score")
def get_ats_score(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    all_job_skills = [s.skill for s in db.scalars(select(JobSkill)).all()]
    ats_result = calculate_ats_score_and_recommendations(user, all_job_skills)
    return ats_result

