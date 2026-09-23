from __future__ import annotations
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.models import Job, User


def generate_cold_email_and_cover_letter(user: User, job: Job) -> dict[str, str]:
    """
    Generates a personalized, highly professional recruiter cold email
    and formal cover letter tailored to the student's profile and job details.
    """
    user_name = user.name or "Job Applicant"
    user_branch = user.branch or "Computer Science / Engineering"
    user_year = f"Year {user.year}" if user.year else "Final Year Student"
    user_skills = [s.skill for s in user.skills] if user.skills else ["Software Development", "Problem Solving"]
    skills_str = ", ".join(user_skills[:5])

    job_title = job.title
    company_name = job.company
    job_location = job.location or "Remote"

    subject = f"Application for {job_title} Position - {user_name}"

    cold_email_body = f"""Dear Hiring Manager / HR Team at {company_name},

I hope this email finds you well.

My name is {user_name}, a {user_year} studying {user_branch}. I recently came across the opening for the {job_title} role at {company_name} in {job_location}, and I am extremely excited to express my interest.

Based on my background, I have developed strong hands-on experience in {skills_str}. I have built multiple end-to-end projects and thrive in fast-paced environments where clean code, continuous learning, and teamwork are valued.

Given {company_name}'s stellar work in this space, I am confident I can contribute effectively to your team's upcoming goals. 

I would welcome the opportunity to connect for a brief 10-minute conversation to discuss how my technical skills and enthusiasm align with your team's requirements.

Thank you for your time and consideration.

Best regards,

{user_name}
{user_branch} Student
Direct Link: {job.apply_url}
"""

    cover_letter = f"""Dear Selection Committee,

Re: Application for {job_title} (Source: {job.source.upper() if job.source else 'Direct'})

I am writing to formally submit my application for the {job_title} position at {company_name}. As a dedicated student majoring in {user_branch} ({user_year}), I possess a strong technical foundation in {skills_str}, combined with a passion for problem-solving and software engineering excellence.

During my academic coursework and project development, I have consistently demonstrated leadership, analytical rigor, and an ability to deliver high-quality solutions. The chance to contribute to {company_name} aligns perfectly with my long-term career aspirations.

Key Qualifications I Bring to {company_name}:
• Technical Proficiency: Core competencies in {skills_str}.
• Domain Relevance: Hands-on project experience in {job_title} workflows.
• Adaptability: Quick learner adept at acquiring new frameworks, tools, and industry best practices.

I am eager to bring my work ethic and technical capabilities to {company_name}. Attached is my resume for your review. I look forward to discussing my application with you in an interview.

Sincerely,

{user_name}
"""

    return {
        "subject": subject,
        "cold_email": cold_email_body,
        "cover_letter": cover_letter,
    }


def calculate_ats_score_and_recommendations(user: User, all_jobs_skills: list[str]) -> dict[str, Any]:
    """
    Calculates an ATS (Applicant Tracking System) Compatibility Score (0-100%)
    for the student's profile compared against current market job requirements.
    """
    user_skills = {s.skill.strip().lower() for s in user.skills} if user.skills else set()
    market_skills = [s.strip().lower() for s in all_jobs_skills if s and s.strip()]

    if not market_skills:
        market_skills = ["python", "javascript", "react", "fastapi", "sql", "git", "html", "css", "data analysis", "docker"]

    skill_counts: dict[str, int] = {}
    for skill in market_skills:
        skill_counts[skill] = skill_counts.get(skill, 0) + 1

    sorted_market = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)
    top_market_skills = [item[0] for item in sorted_market[:15]]

    matching = [s for s in top_market_skills if s in user_skills]
    missing = [s for s in top_market_skills if s not in user_skills]

    if not top_market_skills:
        score = 70.0
    else:
        score = round((len(matching) / len(top_market_skills)) * 100, 1)

    if user.branch:
        score += 5
    if user.year:
        score += 5
    if user.cgpa and user.cgpa >= 7.0:
        score += 5

    score = min(98.0, max(25.0, score))

    if score >= 80:
        rating = "Excellent ATS Optimization"
        color = "#15803d"
    elif score >= 60:
        rating = "Good Resume Visibility"
        color = "#2563eb"
    else:
        rating = "Needs Skill Optimization"
        color = "#d97706"

    return {
        "ats_score": round(score, 1),
        "rating": rating,
        "color": color,
        "matching_top_skills": [s.title() for s in matching],
        "recommended_keywords": [s.title() for s in missing[:6]],
    }
