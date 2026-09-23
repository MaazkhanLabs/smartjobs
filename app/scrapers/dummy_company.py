import httpx
from bs4 import BeautifulSoup

from app.schemas import JobCreate


DUMMY_URL = "https://example.com/jobs"


async def scrape_dummy_company() -> list[JobCreate]:
    """
    Skeleton only.

    Replace DUMMY_URL with a company career page that you are permitted
    to scrape. Inspect its HTML and change the CSS selectors accordingly.
    """

    async with httpx.AsyncClient(
        timeout=20,
        follow_redirects=True,
        headers={
            "User-Agent": "StudentJobAggregator/1.0"
        },
    ) as client:
        try:
            response = await client.get(DUMMY_URL)
            response.raise_for_status()
            html_text = response.text
        except Exception:
            # Fallback for offline/demo environment
            html_text = ""

    if not html_text:
        return []

    soup = BeautifulSoup(html_text, "html.parser")

    jobs: list[JobCreate] = []

    # Example selectors. These are intentionally placeholders.
    for card in soup.select(".job-card"):
        title_node = card.select_one(".job-title")
        company_node = card.select_one(".company")
        location_node = card.select_one(".location")
        link_node = card.select_one("a")

        if not title_node or not link_node:
            continue

        apply_url = link_node.get("href")
        if not apply_url:
            continue

        jobs.append(
            JobCreate(
                title=title_node.get_text(" ", strip=True),
                company=(
                    company_node.get_text(" ", strip=True)
                    if company_node
                    else "Dummy Company"
                ),
                location=(
                    location_node.get_text(" ", strip=True)
                    if location_node
                    else ""
                ),
                description=card.get_text(" ", strip=True),
                apply_url=apply_url,
                source="dummy_company",
                external_id=apply_url,
                skills=[],
            )
        )

    return jobs
