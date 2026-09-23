import re

from app.schemas import JobCreate


def extract(pattern: str, text: str, default: str = "") -> str:
    match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
    return match.group(1).strip() if match else default


def parse_college_email(email_text: str) -> JobCreate:
    title = extract(r"^Title:\s*(.+)$", email_text)
    company = extract(r"^Company:\s*(.+)$", email_text)
    location = extract(r"^Location:\s*(.+)$", email_text)
    work_mode = extract(r"^Work Mode:\s*(.+)$", email_text, "onsite")
    role_type = extract(r"^Role Type:\s*(.+)$", email_text, "internship")

    stipend_text = extract(r"^Stipend:\s*([0-9]+(?:\.[0-9]+)?)$", email_text, "0")
    cgpa_text = extract(
        r"^Minimum CGPA:\s*([0-9]+(?:\.[0-9]+)?)$",
        email_text,
        "",
    )

    branches = extract(r"^Eligible Branches:\s*(.+)$", email_text)
    years = extract(r"^Eligible Years:\s*(.+)$", email_text)
    skills = extract(r"^Skills:\s*(.+)$", email_text)

    apply_url = extract(r"^Apply Link:\s*(\S+)$", email_text)

    description_match = re.search(
        r"Description:\s*(.*)",
        email_text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    description = (
        description_match.group(1).strip()
        if description_match
        else ""
    )

    if not title or not company or not apply_url:
        raise ValueError(
            "Email must contain Title, Company and Apply Link."
        )

    return JobCreate(
        title=title,
        company=company,
        description=description,
        location=location,
        work_mode=work_mode.lower(),
        role_type=role_type.lower(),
        compensation=float(stipend_text),
        min_cgpa=float(cgpa_text) if cgpa_text else None,
        eligible_branches=[
            item.strip() for item in branches.split(",") if item.strip()
        ],
        eligible_years=[
            int(item.strip())
            for item in years.split(",")
            if item.strip().isdigit()
        ],
        skills=[
            item.strip()
            for item in skills.split(",")
            if item.strip()
        ],
        apply_url=apply_url,
        source="college_email",
        external_id=apply_url,
    )
