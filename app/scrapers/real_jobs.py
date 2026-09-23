from __future__ import annotations
import re
import httpx
from bs4 import BeautifulSoup

from app.database import SessionLocal
from app.schemas import JobCreate
from app.services.jobs import create_job
from app.services.recommendations import recompute_for_new_job

COMMON_SKILLS = [
    "python", "javascript", "react", "fastapi", "sql", "html", "css",
    "node.js", "git", "data analysis", "c++", "java", "typescript",
    "docker", "aws", "pandas", "django", "vue", "angular", "express", "cybersecurity",
    "figma", "ui/ux", "seo", "digital marketing", "tableau", "power bi", "flutter",
    "kotlin", "android", "ios", "machine learning", "deep learning", "nlp", "content writing"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}


def extract_skills_from_text(text: str, tags: list[str] | None = None) -> list[str]:
    found = set()
    lowered = text.lower()

    if tags:
        for tag in tags:
            tag_clean = tag.strip().lower()
            if tag_clean in COMMON_SKILLS or len(tag_clean) < 15:
                found.add(tag_clean)

    for skill in COMMON_SKILLS:
        if re.search(rf"\b{re.escape(skill)}\b", lowered):
            found.add(skill)

    return list(found)


def clean_html(raw_html: str) -> str:
    if not raw_html:
        return ""
    soup = BeautifulSoup(raw_html, "html.parser")
    return soup.get_text(separator=" ", strip=True)


async def search_live_jobs_on_demand(query: str) -> list[JobCreate]:
    """Dynamically query LinkedIn and Internshala in real-time for any user search term."""
    if not query or len(query.strip()) < 2:
        return []

    clean_q = query.strip().lower()
    encoded_q = clean_q.replace(" ", "%20")
    jobs: list[JobCreate] = []

    try:
        async with httpx.AsyncClient(timeout=10, headers=HEADERS, follow_redirects=True) as client:
            # 1. LinkedIn Live Search
            linkedin_url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={encoded_q}&location=India"
            try:
                r1 = await client.get(linkedin_url)
                if r1.status_code == 200:
                    soup = BeautifulSoup(r1.text, "html.parser")
                    cards = soup.select("li")
                    for card in cards[:10]:
                        title_elem = card.select_one(".base-search-card__title")
                        company_elem = card.select_one(".base-search-card__subtitle")
                        location_elem = card.select_one(".job-search-card__location")
                        link_elem = card.select_one("a.base-card__full-link")

                        if not title_elem or not link_elem:
                            continue

                        title = title_elem.get_text(strip=True)
                        company = company_elem.get_text(strip=True) if company_elem else "LinkedIn Employer"
                        location = location_elem.get_text(strip=True) if location_elem else "India"
                        raw_apply_url = link_elem.get("href", "")
                        direct_apply_url = raw_apply_url.split("?")[0] if raw_apply_url else ""

                        if not direct_apply_url:
                            continue

                        extracted_skills = extract_skills_from_text(f"{title} {clean_q}")
                        role_kind = "internship" if "intern" in title.lower() or "intern" in clean_q else "entry-level"

                        jobs.append(
                            JobCreate(
                                title=title,
                                company=company,
                                description=f"Direct job listing from LinkedIn for {title} at {company} in {location}.",
                                location=location,
                                work_mode="onsite" if "remote" not in location.lower() else "remote",
                                role_type=role_kind,
                                compensation=0.0,
                                min_cgpa=6.0,
                                eligible_branches=["Computer Science", "IT", "Data Science", "Business", "Design", "Management"],
                                eligible_years=[1, 2, 3, 4],
                                skills=extracted_skills,
                                apply_url=direct_apply_url,
                                source="linkedin",
                                external_id=direct_apply_url,
                            )
                        )
            except Exception:
                pass

            # 2. Internshala Live Search
            internshala_cat = clean_q.replace(" ", "-") + "-internship"
            internshala_url = f"https://internshala.com/internships/{internshala_cat}"
            try:
                r2 = await client.get(internshala_url)
                if r2.status_code == 200:
                    soup = BeautifulSoup(r2.text, "html.parser")
                    cards = soup.select(".individual_internship")
                    for card in cards[:10]:
                        title_elem = card.select_one(".job-internship-name") or card.select_one(".profile")
                        company_elem = card.select_one(".company-name") or card.select_one(".company_name")
                        location_elem = card.select_one(".location_link") or card.select_one("#location_names")
                        stipend_elem = card.select_one(".stipend")

                        rel_link = card.get("data-href") or (card.select_one("a").get("href") if card.select_one("a") else "")

                        if not title_elem or not rel_link:
                            continue

                        title = title_elem.get_text(strip=True)
                        company = company_elem.get_text(strip=True) if company_elem else "Internshala Employer"
                        location = location_elem.get_text(strip=True) if location_elem else "India"
                        stipend_text = stipend_elem.get_text(strip=True) if stipend_elem else "0"

                        direct_apply_url = f"https://internshala.com{rel_link}" if rel_link.startswith("/") else rel_link

                        stipend_match = re.search(r"₹\s*([0-9,]+)", stipend_text)
                        stipend_val = float(stipend_match.group(1).replace(",", "")) if stipend_match else 0.0

                        extracted_skills = extract_skills_from_text(f"{title} {clean_q}")

                        jobs.append(
                            JobCreate(
                                title=title,
                                company=company,
                                description=f"Direct internship posting from Internshala for {title} at {company}. Stipend: {stipend_text}.",
                                location=location,
                                work_mode="remote" if "work from home" in location.lower() else "onsite",
                                role_type="internship",
                                compensation=stipend_val,
                                min_cgpa=6.0,
                                eligible_branches=["Computer Science", "IT", "Data Science", "Design", "Business", "Management"],
                                eligible_years=[1, 2, 3, 4],
                                skills=extracted_skills,
                                apply_url=direct_apply_url,
                                source="internshala",
                                external_id=direct_apply_url,
                            )
                        )
            except Exception:
                pass
    except Exception as exc:
        print(f"Error in on-demand live search: {exc}")

    # Store found live jobs into DB
    if jobs:
        db = SessionLocal()
        try:
            for job_data in jobs:
                job = create_job(db, job_data)
                if job:
                    recompute_for_new_job(db, job)
        finally:
            db.close()

    return jobs


async def fetch_linkedin_jobs() -> list[JobCreate]:
    """Fetch direct LinkedIn job postings across diverse tech, business, design & management roles."""
    search_terms = [
        "python developer", "frontend developer", "web developer intern", "data analyst",
        "full stack developer", "software engineer intern", "cyber security intern",
        "ui ux designer", "data scientist intern", "devops engineer", "product management intern",
        "digital marketing intern", "business development intern", "hr intern",
        "mobile app developer", "qa engineer"
    ]
    jobs: list[JobCreate] = []

    try:
        async with httpx.AsyncClient(timeout=12, headers=HEADERS, follow_redirects=True) as client:
            for term in search_terms:
                encoded_term = term.replace(" ", "%20")
                url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={encoded_term}&location=India"
                try:
                    response = await client.get(url)
                    if response.status_code != 200:
                        continue

                    soup = BeautifulSoup(response.text, "html.parser")
                    cards = soup.select("li")

                    for card in cards[:6]:
                        title_elem = card.select_one(".base-search-card__title")
                        company_elem = card.select_one(".base-search-card__subtitle")
                        location_elem = card.select_one(".job-search-card__location")
                        link_elem = card.select_one("a.base-card__full-link")

                        if not title_elem or not link_elem:
                            continue

                        title = title_elem.get_text(strip=True)
                        company = company_elem.get_text(strip=True) if company_elem else "LinkedIn Employer"
                        location = location_elem.get_text(strip=True) if location_elem else "India"
                        raw_apply_url = link_elem.get("href", "")
                        direct_apply_url = raw_apply_url.split("?")[0] if raw_apply_url else ""

                        if not direct_apply_url:
                            continue

                        extracted_skills = extract_skills_from_text(f"{title} {term}")
                        role_kind = "internship" if "intern" in title.lower() or "intern" in term else "entry-level"

                        jobs.append(
                            JobCreate(
                                title=title,
                                company=company,
                                description=f"Direct job listing from LinkedIn for {title} at {company} in {location}.",
                                location=location,
                                work_mode="onsite" if "remote" not in location.lower() else "remote",
                                role_type=role_kind,
                                compensation=0.0,
                                min_cgpa=6.0,
                                eligible_branches=["Computer Science", "IT", "Data Science", "Business", "Design", "Management"],
                                eligible_years=[1, 2, 3, 4],
                                skills=extracted_skills,
                                apply_url=direct_apply_url,
                                source="linkedin",
                                external_id=direct_apply_url,
                            )
                        )
                except Exception:
                    continue
    except Exception as exc:
        print(f"Error fetching LinkedIn jobs: {exc}")

    return jobs


async def fetch_internshala_jobs() -> list[JobCreate]:
    """Fetch direct Internshala internship postings across multiple categories."""
    categories = [
        "computer-science-internship",
        "python-django-internship",
        "web-development-internship",
        "data-science-internship",
        "ui-ux-design-internship",
        "digital-marketing-internship",
        "business-development-internship",
        "mobile-app-development-internship",
        "human-resources-hr-internship",
        "finance-internship",
    ]
    jobs: list[JobCreate] = []

    try:
        async with httpx.AsyncClient(timeout=12, headers=HEADERS, follow_redirects=True) as client:
            for cat in categories:
                url = f"https://internshala.com/internships/{cat}"
                try:
                    response = await client.get(url)
                    if response.status_code != 200:
                        continue

                    soup = BeautifulSoup(response.text, "html.parser")
                    cards = soup.select(".individual_internship")

                    for card in cards[:5]:
                        title_elem = card.select_one(".job-internship-name") or card.select_one(".profile")
                        company_elem = card.select_one(".company-name") or card.select_one(".company_name")
                        location_elem = card.select_one(".location_link") or card.select_one("#location_names")
                        stipend_elem = card.select_one(".stipend")

                        rel_link = card.get("data-href") or (card.select_one("a").get("href") if card.select_one("a") else "")

                        if not title_elem or not rel_link:
                            continue

                        title = title_elem.get_text(strip=True)
                        company = company_elem.get_text(strip=True) if company_elem else "Internshala Employer"
                        location = location_elem.get_text(strip=True) if location_elem else "Mumbai"
                        stipend_text = stipend_elem.get_text(strip=True) if stipend_elem else "0"

                        direct_apply_url = f"https://internshala.com{rel_link}" if rel_link.startswith("/") else rel_link

                        stipend_match = re.search(r"₹\s*([0-9,]+)", stipend_text)
                        stipend_val = float(stipend_match.group(1).replace(",", "")) if stipend_match else 0.0

                        extracted_skills = extract_skills_from_text(f"{title} {cat}")

                        jobs.append(
                            JobCreate(
                                title=title,
                                company=company,
                                description=f"Direct internship posting from Internshala for {title} at {company}. Stipend: {stipend_text}.",
                                location=location,
                                work_mode="remote" if "work from home" in location.lower() else "onsite",
                                role_type="internship",
                                compensation=stipend_val,
                                min_cgpa=6.0,
                                eligible_branches=["Computer Science", "IT", "Data Science", "Design", "Business", "Management"],
                                eligible_years=[1, 2, 3, 4],
                                skills=extracted_skills,
                                apply_url=direct_apply_url,
                                source="internshala",
                                external_id=direct_apply_url,
                            )
                        )
                except Exception:
                    continue
    except Exception as exc:
        print(f"Error fetching Internshala jobs: {exc}")

    return jobs


async def fetch_remotive_jobs() -> list[JobCreate]:
    """Fetch direct Remotive job postings across categories."""
    remotive_categories = ["software-dev", "design", "data", "devops", "product", "marketing", "business"]
    jobs: list[JobCreate] = []

    try:
        async with httpx.AsyncClient(timeout=12, follow_redirects=True) as client:
            for cat in remotive_categories:
                url = f"https://remotive.com/api/remote-jobs?category={cat}&limit=10"
                try:
                    response = await client.get(url)
                    if response.status_code != 200:
                        continue
                    data = response.json().get("jobs", [])

                    for item in data:
                        title = item.get("title", "").strip()
                        company = item.get("company_name", "Remote Company").strip()
                        apply_url = item.get("url", "")
                        raw_desc = item.get("description", "")
                        clean_desc = clean_html(raw_desc)[:1000]
                        tags = item.get("tags", [])

                        if not title or not apply_url:
                            continue

                        extracted_skills = extract_skills_from_text(f"{title} {clean_desc}", tags)
                        role_kind = "internship" if "intern" in title.lower() else "entry-level"

                        jobs.append(
                            JobCreate(
                                title=title,
                                company=company,
                                description=clean_desc,
                                location=item.get("candidate_required_location", "Remote") or "Remote",
                                work_mode="remote",
                                role_type=role_kind,
                                compensation=0.0,
                                min_cgpa=6.0,
                                eligible_branches=["Computer Science", "IT", "Data Science", "Design", "Business", "Management"],
                                eligible_years=[1, 2, 3, 4],
                                skills=extracted_skills,
                                apply_url=apply_url,
                                source="remotive",
                                external_id=str(item.get("id", apply_url)),
                            )
                        )
                except Exception:
                    continue
    except Exception as exc:
        print(f"Error fetching Remotive jobs: {exc}")

    return jobs


async def fetch_arbeitnow_jobs() -> list[JobCreate]:
    """Fetch direct Arbeitnow job postings."""
    url = "https://www.arbeitnow.com/api/job-board-api"
    jobs: list[JobCreate] = []

    try:
        async with httpx.AsyncClient(timeout=12, follow_redirects=True) as client:
            response = await client.get(url)
            if response.status_code != 200:
                return []
            data = response.json().get("data", [])

        for item in data[:30]:
            title = item.get("title", "").strip()
            company = item.get("company_name", "Tech Company").strip()
            apply_url = item.get("url", "")
            raw_desc = item.get("description", "")
            clean_desc = clean_html(raw_desc)[:1000]
            tags = item.get("tags", [])
            is_remote = item.get("remote", False)
            location = item.get("location", "Global") or "Remote"

            if not title or not apply_url:
                continue

            extracted_skills = extract_skills_from_text(f"{title} {clean_desc}", tags)
            role_kind = "internship" if "intern" in title.lower() else "entry-level"

            jobs.append(
                JobCreate(
                    title=title,
                    company=company,
                    description=clean_desc,
                    location=location,
                    work_mode="remote" if is_remote else "hybrid",
                    role_type=role_kind,
                    compensation=0.0,
                    min_cgpa=6.0,
                    eligible_branches=["Computer Science", "IT", "Data Science", "Design", "Business", "Management"],
                    eligible_years=[1, 2, 3, 4],
                    skills=extracted_skills,
                    apply_url=apply_url,
                    source="arbeitnow",
                    external_id=item.get("slug", apply_url),
                )
            )
    except Exception as exc:
        print(f"Error fetching Arbeitnow jobs: {exc}")

    return jobs


async def fetch_and_store_real_jobs() -> int:
    linkedin_jobs = await fetch_linkedin_jobs()
    internshala_jobs = await fetch_internshala_jobs()
    remotive_jobs = await fetch_remotive_jobs()
    arbeitnow_jobs = await fetch_arbeitnow_jobs()

    all_jobs = linkedin_jobs + internshala_jobs + remotive_jobs + arbeitnow_jobs
    if not all_jobs:
        return 0

    db = SessionLocal()
    inserted_count = 0

    try:
        for job_data in all_jobs:
            job = create_job(db, job_data)
            if job:
                recompute_for_new_job(db, job)
                inserted_count += 1
    finally:
        db.close()

    return inserted_count
