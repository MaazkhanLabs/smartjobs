from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.dependencies import get_current_user
from app.models import User

router = APIRouter(tags=["web"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return RedirectResponse("/dashboard")


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
    )


@router.get("/signup", response_class=HTMLResponse)
def signup_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="signup.html",
    )


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(
    request: Request,
    user: User = Depends(get_current_user),
):
    if user.is_admin:
        return RedirectResponse("/admin")
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={"user": user},
    )


@router.get("/profile", response_class=HTMLResponse)
def profile_page(
    request: Request,
    user: User = Depends(get_current_user),
):
    return templates.TemplateResponse(
        request=request,
        name="profile.html",
        context={"user": user},
    )


@router.get("/applications", response_class=HTMLResponse)
def applications_page(
    request: Request,
    user: User = Depends(get_current_user),
):
    return templates.TemplateResponse(
        request=request,
        name="applications.html",
        context={"user": user},
    )


@router.get("/analytics", response_class=HTMLResponse)
def analytics_page(
    request: Request,
    user: User = Depends(get_current_user),
):
    return templates.TemplateResponse(
        request=request,
        name="analytics.html",
        context={"user": user},
    )




@router.get("/jobs/{job_id}", response_class=HTMLResponse)
def job_detail_page(
    request: Request,
    job_id: int,
    user: User = Depends(get_current_user),
):
    return templates.TemplateResponse(
        request=request,
        name="job_detail.html",
        context={"job_id": job_id},
    )


@router.get("/survey", response_class=HTMLResponse)
def survey_page(
    request: Request,
    user: User = Depends(get_current_user),
):
    return templates.TemplateResponse(
        request=request,
        name="survey.html",
        context={"user": user},
    )


@router.get("/admin", response_class=HTMLResponse)
def admin_page(
    request: Request,
    user: User = Depends(get_current_user),
):
    return templates.TemplateResponse(
        request=request,
        name="admin.html",
        context={"user": user},
    )
