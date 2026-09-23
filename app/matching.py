from app.models import Job, User


def csv_values(value: str | None) -> set[str]:
    if not value:
        return set()

    return {
        item.strip().lower()
        for item in value.split(",")
        if item.strip()
    }


def normalized_values(values: str | list[str] | None) -> set[str]:
    if not values:
        return set()
    if isinstance(values, str):
        return csv_values(values)
    return {
        value.strip().lower()
        for value in values
        if value and value.strip()
    }


def calculate_match(user: User, job: Job) -> tuple[float, str]:
    """
    Transparent 0-1 recommendation score.

    Components:
      1. Eligibility: 0.40
      2. Skill overlap: 0.30
      3. Role preference: 0.10
      4. Location/work-mode preference: 0.10
      5. Compensation preference: 0.10

    Eligibility is treated as a gate:
      - If CGPA is below required CGPA -> score 0
      - If branch is explicitly restricted and does not match -> score 0
      - If year is explicitly restricted and does not match -> score 0

    For eligible users:
      final score =
        0.40 * eligibility_score
        + 0.30 * skill_score
        + 0.10 * role_score
        + 0.10 * preference_score
        + 0.10 * compensation_score

    The explanation returned with the recommendation makes the result
    understandable to the student.
    """

    reasons: list[str] = []

    # -----------------------------
    # 1. Hard eligibility
    # -----------------------------
    if job.min_cgpa is not None:
        if user.cgpa is None:
            return 0.0, "CGPA is required for this opportunity."
        if user.cgpa < job.min_cgpa:
            return 0.0, f"CGPA {user.cgpa:.2f} is below required {job.min_cgpa:.2f}."

    allowed_branches = csv_values(job.eligible_branches)
    if allowed_branches and user.branch:
        if user.branch.lower().strip() not in allowed_branches:
            return 0.0, "Your branch is not listed as eligible."

    allowed_years = csv_values(job.eligible_years)
    if allowed_years and user.year is not None:
        if str(user.year) not in allowed_years:
            return 0.0, "Your academic year is not listed as eligible."

    eligibility_score = 1.0
    reasons.append("Eligible")

    # -----------------------------
    # 2. Skill overlap
    # -----------------------------
    user_skills = {skill.skill.strip().lower() for skill in user.skills}
    job_skills = {skill.skill.strip().lower() for skill in job.skills}

    if job_skills:
        matched_skills = user_skills.intersection(job_skills)
        skill_score = len(matched_skills) / len(job_skills)

        if matched_skills:
            reasons.append(
                "Skills: " + ", ".join(sorted(matched_skills))
            )
    else:
        skill_score = 0.5
        reasons.append("No structured skill requirements supplied")

    # -----------------------------
    # 3. Role preference
    # -----------------------------
    preferences = user.preferences

    preferred_roles = (
        normalized_values(preferences.roles)
        if preferences
        else set()
    )

    if preferred_roles:
        job_role_text = f"{job.title} {job.role_type}".lower()
        role_match = any(role in job_role_text for role in preferred_roles)
        role_score = 1.0 if role_match else 0.0
        if role_match:
            reasons.append("Role preference matched")
    else:
        role_score = 0.5

    # -----------------------------
    # 4. Location/work-mode
    # -----------------------------
    preferred_locations = (
        normalized_values(preferences.locations)
        if preferences
        else set()
    )
    preferred_mode = preferences.work_mode if preferences else "any"

    location_match = False
    if preferred_locations:
        job_location = job.location.lower()
        location_match = any(
            location in job_location
            for location in preferred_locations
        )

    mode_match = (
        preferred_mode == "any"
        or preferred_mode.lower() == job.work_mode.lower()
    )

    if preferred_locations or preferred_mode != "any":
        preference_score = (
            (1.0 if location_match else 0.0)
            + (1.0 if mode_match else 0.0)
        ) / (
            (1 if preferred_locations else 0)
            + (1 if preferred_mode != "any" else 0)
        )
    else:
        preference_score = 0.5

    if location_match:
        reasons.append("Location preference matched")
    if mode_match and preferred_mode != "any":
        reasons.append("Work-mode preference matched")

    # -----------------------------
    # 5. Compensation
    # -----------------------------
    minimum = preferences.min_compensation if preferences else 0

    if minimum <= 0:
        compensation_score = 0.5
    elif job.compensation >= minimum:
        compensation_score = 1.0
        reasons.append("Compensation meets minimum")
    else:
        compensation_score = max(0.0, job.compensation / minimum)

    score = (
        0.40 * eligibility_score
        + 0.30 * skill_score
        + 0.10 * role_score
        + 0.10 * preference_score
        + 0.10 * compensation_score
    )

    score = max(0.0, min(1.0, score))

    explanation = (
        f"Score {score:.2f}. "
        + "; ".join(reasons)
        + "."
    )

    return score, explanation


def get_skill_gap_analysis(user: User, job: Job) -> dict:
    user_skills = {skill.skill.strip().lower() for skill in user.skills}
    job_skills = {skill.skill.strip().lower() for skill in job.skills}

    matching = sorted(list(user_skills.intersection(job_skills)))
    missing = sorted(list(job_skills.difference(user_skills)))

    return {
        "user_skills": sorted(list(user_skills)),
        "job_skills": sorted(list(job_skills)),
        "matching_skills": matching,
        "missing_skills": missing,
        "match_percentage": round((len(matching) / len(job_skills) * 100) if job_skills else 100, 1)
    }

