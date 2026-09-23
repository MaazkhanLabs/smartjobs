from app.database import Base, SessionLocal, engine
from app.models import Job, JobSkill, User, UserPreference, UserSkill
from app.auth import hash_password


def seed():
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        user = db.query(User).filter(
            User.email == "student@example.com"
        ).first()

        if not user:
            user = User(
                name="Demo Student",
                email="student@example.com",
                password_hash=hash_password("password123"),
                branch="Computer Science",
                year=1,
                cgpa=6.5,
            )
            db.add(user)
            db.flush()

            user.preferences = UserPreference(
                roles="frontend developer,python developer,web developer",
                locations="mumbai,remote,pune",
                work_mode="any",
                min_compensation=5000,
            )

            for skill in [
                "javascript",
                "python",
                "html",
                "css",
                "fastapi",
                "sql",
            ]:
                db.add(
                    UserSkill(
                        user_id=user.id,
                        skill=skill,
                    )
                )

        # Clear existing seed jobs to update schema cleanly
        db.query(JobSkill).delete()
        db.query(Job).delete()
        db.commit()

        jobs = [
            Job(
                title="Frontend Developer Intern",
                company="Apex Web Studios",
                description="Build responsive web interfaces using HTML, CSS, JavaScript, and React.",
                location="Mumbai",
                work_mode="onsite",
                role_type="internship",
                compensation=12000,
                min_cgpa=6.0,
                eligible_branches="Computer Science,IT,Computer Applications",
                eligible_years="1,2,3,4",
                apply_url="https://remotive.com/remote-jobs/software-dev",
                source="seed",
                external_id="seed-frontend-mumbai",
            ),
            Job(
                title="Python Backend Intern",
                company="ABC Technologies",
                description="Build RESTful APIs and internal tools using Python and FastAPI.",
                location="Mumbai",
                work_mode="hybrid",
                role_type="internship",
                compensation=15000,
                min_cgpa=6.5,
                eligible_branches="Computer Science,IT",
                eligible_years="1,2,3,4",
                apply_url="https://www.arbeitnow.com/jobs/browse",
                source="seed",
                external_id="seed-python-mumbai",
            ),
            Job(
                title="Web Developer Intern",
                company="Digital Horizon",
                description="Develop modern web portals, optimize user experience, and write clean Javascript.",
                location="Mumbai",
                work_mode="remote",
                role_type="internship",
                compensation=10000,
                min_cgpa=6.0,
                eligible_branches="Computer Science,IT,Electronics",
                eligible_years="1,2,3,4",
                apply_url="https://remotive.com/remote-jobs/software-dev",
                source="seed",
                external_id="seed-web-mumbai",
            ),
            Job(
                title="Frontend Developer Intern",
                company="Demo Web Labs",
                description="Build UI components and frontend application flows.",
                location="Pune",
                work_mode="onsite",
                role_type="internship",
                compensation=10000,
                min_cgpa=6.5,
                eligible_branches="Computer Science,IT",
                eligible_years="1,2,3,4",
                apply_url="https://www.arbeitnow.com/jobs/browse",
                source="seed",
                external_id="seed-frontend-pune",
            ),
            Job(
                title="Data Analyst Intern",
                company="Insight Analytics",
                description="Perform data analysis, query databases using SQL, and build visual dashboards.",
                location="Remote",
                work_mode="remote",
                role_type="internship",
                compensation=14000,
                min_cgpa=6.5,
                eligible_branches="Computer Science,IT,Data Science",
                eligible_years="1,2,3,4",
                apply_url="https://remotive.com/remote-jobs/data",
                source="seed",
                external_id="seed-data-analyst",
            ),
            Job(
                title="Full Stack Intern",
                company="Tech Solutions India",
                description="Work across frontend JavaScript interfaces and Python backend services.",
                location="Mumbai",
                work_mode="onsite",
                role_type="internship",
                compensation=16000,
                min_cgpa=6.5,
                eligible_branches="Computer Science,IT",
                eligible_years="1,2,3,4",
                apply_url="https://remotive.com/remote-jobs/software-dev",
                source="seed",
                external_id="seed-fullstack-mumbai",
            ),
            Job(
                title="Software Engineering Intern",
                company="Cloud Scale Systems",
                description="Learn cloud infrastructure, API engineering, and distributed systems.",
                location="Remote",
                work_mode="remote",
                role_type="internship",
                compensation=20000,
                min_cgpa=7.0,
                eligible_branches="Computer Science,IT",
                eligible_years="1,2,3,4",
                apply_url="https://remotive.com/remote-jobs/software-dev",
                source="seed",
                external_id="seed-swe-intern",
            ),
        ]

        db.add_all(jobs)
        db.flush()

        skills_map = {
            "Frontend Developer Intern": ["javascript", "html", "css"],
            "Python Backend Intern": ["python", "fastapi", "sql", "git"],
            "Web Developer Intern": ["javascript", "html", "css"],
            "Data Analyst Intern": ["python", "sql", "pandas"],
            "Full Stack Intern": ["javascript", "python", "sql", "html", "css"],
            "Software Engineering Intern": ["python", "sql", "git"],
        }

        for job in jobs:
            for skill in skills_map.get(job.title, []):
                db.add(
                    JobSkill(
                        job_id=job.id,
                        skill=skill,
                    )
                )

        db.commit()

        # Compute recommendations for all users
        from app.services.recommendations import recompute_for_all_users

        recompute_for_all_users(db)

        print("Updated seed data with functional application URLs!")

    finally:
        db.close()


if __name__ == "__main__":
    seed()
