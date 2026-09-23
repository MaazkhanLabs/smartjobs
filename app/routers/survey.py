from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import SurveyResponse, User
from app.schemas import SurveyCreate

router = APIRouter(prefix="/api/survey", tags=["survey"])


@router.post("")
def submit_survey(
    data: SurveyCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    response = SurveyResponse(
        user_id=user.id,
        helped_find_relevant=data.helped_find_relevant,
        applied_more=data.applied_more,
        comments=data.comments,
    )

    db.add(response)
    db.commit()

    return {"message": "Survey submitted. Thank you!"}
