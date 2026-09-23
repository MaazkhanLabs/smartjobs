from fastapi import APIRouter, Depends, Form, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import create_access_token, hash_password, verify_password
from app.database import get_db
from app.dependencies import get_current_user
from app.models import User, UserPreference
from app.schemas import UserLogin, UserSignup

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/signup")
def signup(
    data: UserSignup,
    response: Response,
    db: Session = Depends(get_db),
):
    email = data.email.lower()

    existing = db.scalar(
        select(User).where(User.email == email)
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Email already registered",
        )

    user = User(
        name=data.name,
        email=email,
        password_hash=hash_password(data.password),
        branch=data.branch,
        year=data.year,
        cgpa=data.cgpa,
    )

    db.add(user)
    db.flush()

    db.add(UserPreference(user_id=user.id))
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id)

    response.set_cookie(
        "access_token",
        token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=60 * 60 * 24,
    )

    return {"message": "Account created", "user_id": user.id}


@router.post("/login")
def login(
    data: UserLogin,
    response: Response,
    db: Session = Depends(get_db),
):
    user = db.scalar(
        select(User).where(User.email == data.email.lower())
    )

    if not user or not verify_password(
        data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    token = create_access_token(user.id)

    response.set_cookie(
        "access_token",
        token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=60 * 60 * 24,
    )

    return {"message": "Logged in", "is_admin": user.is_admin}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logged out"}


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "branch": user.branch,
        "year": user.year,
        "cgpa": user.cgpa,
    }
