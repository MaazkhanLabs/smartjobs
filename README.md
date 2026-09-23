# Smart Internship & Job Aggregator for College Students

A complete, production-ready final-year project designed to aggregate, match, and recommend internship and job opportunities tailored specifically to college students.

## Features

- **Personalized Recommendations**: Deterministic 0-1 transparent matching algorithm considering CGPA eligibility, academic year, branch, skill overlap, location, work-mode preference, and minimum stipend.
- **Multi-Source Aggregation**:
  - Manual Job Entry API for Admins
  - Regex-based Plain-Text College Email Parser
  - Web Scraper Skeleton (BeautifulSoup4 + HTTPX)
  - Telegram Channel / Message Ingestion Framework
- **FastAPI Web Application**: Server-rendered Jinja2 templates styled with modern CSS.
- **Student Profile Management**: Manage skills, preferences, CGPA, branch, and academic year.
- **Telegram Bot**: `/start`, `/profile`, `/jobs`, `/alerts on|off` and daily digest updates.
- **Analytics & Research Surveys**: Event tracking (views, apply clicks, saved) and student survey submission.

---

## Quickstart Guide

### 1. Setup Virtual Environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Seed Database

```bash
python -m scripts.seed
```

Demo Account Credentials:
- **Email**: `student@example.com`
- **Password**: `password123`

### 4. Run Development Server

```bash
uvicorn app.main:app --reload
```

Open your browser at `http://127.0.0.1:8000` to access the dashboard.
API documentation is available at `http://127.0.0.1:8000/docs`.

---

## Running Tests

```bash
pytest
```

---

## Project Structure

```text
smart-job-aggregator/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── auth.py
│   ├── matching.py
│   ├── dependencies.py
│   ├── services/
│   ├── scrapers/
│   ├── telegram/
│   ├── routers/
│   ├── templates/
│   └── static/
├── scripts/
│   ├── seed.py
│   ├── compute_recommendations.py
│   └── analytics.py
├── tests/
│   ├── test_matching.py
│   └── test_auth.py
├── requirements.txt
└── IMPLEMENTATION.md
```
