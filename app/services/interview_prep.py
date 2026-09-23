from __future__ import annotations

SKILL_QUESTIONS: dict[str, list[dict[str, str]]] = {
    "python": [
        {
            "question": "What is the difference between list, tuple, and set in Python?",
            "tip": "Explain mutability (lists are mutable, tuples immutable) and uniqueness (sets store unique items with fast O(1) hash lookup)."
        },
        {
            "question": "How do decorators work in Python, and when would you use one?",
            "tip": "Mention high-order functions, logging, authentication, and wrapping function behavior using @decorator syntax."
        }
    ],
    "fastapi": [
        {
            "question": "How does FastAPI achieve high performance using Python async/await and Pydantic?",
            "tip": "Highlight Starlette ASGI foundation, non-blocking asynchronous event loop, and automated OpenAPI validation via Pydantic."
        },
        {
            "question": "How do Dependency Injection (Depends) and HTTP-only cookie auth work in FastAPI?",
            "tip": "Explain reusable dependency functions for database sessions, current user extraction, and token verification."
        }
    ],
    "javascript": [
        {
            "question": "What is the Event Loop in JavaScript and how do Promises differ from setTimeout?",
            "tip": "Explain microtask queue (Promises) having higher priority than macrotask queue (setTimeout timers)."
        },
        {
            "question": "Difference between let, const, and var?",
            "tip": "Talk about block scoping vs function scoping, and hoisting behavior."
        }
    ],
    "react": [
        {
            "question": "What is the Virtual DOM and how does React's reconciliation algorithm work?",
            "tip": "Explain how React builds a virtual tree in memory, diffs it against the old tree, and batches minimal real DOM updates."
        },
        {
            "question": "When should you use useEffect vs useMemo vs useCallback?",
            "tip": "useEffect handles side effects, useMemo caches expensive computation values, useCallback memoizes function references."
        }
    ],
    "sql": [
        {
            "question": "What is the difference between INNER JOIN, LEFT JOIN, and FULL OUTER JOIN?",
            "tip": "Inner join returns matching rows in both tables; left join returns all rows from left table regardless of right table match."
        },
        {
            "question": "What are database indexes, and when do they slow down database performance?",
            "tip": "Indexes speed up SELECT queries via B-Trees, but add overhead during INSERT, UPDATE, and DELETE operations."
        }
    ],
    "docker": [
        {
            "question": "What is the difference between a Docker Image and a Docker Container?",
            "tip": "An image is an immutable template blueprint; a container is a running instance of an image."
        }
    ],
    "aws": [
        {
            "question": "What are the core differences between AWS EC2, S3, and Lambda?",
            "tip": "EC2 is virtual server compute, S3 is object cloud storage, Lambda is serverless event-driven execution."
        }
    ],
    "ui/ux": [
        {
            "question": "How do you conduct user research before designing a new feature?",
            "tip": "Mention user interviews, journey mapping, wireframing in Figma, and usability testing iterations."
        }
    ],
    "digital marketing": [
        {
            "question": "How do you measure CAC (Customer Acquisition Cost) vs LTV (Lifetime Value)?",
            "tip": "LTV:CAC ratio should ideally be 3:1 or higher for sustainable organic growth."
        }
    ]
}

GENERAL_QUESTIONS = [
    {
        "question": "Tell me about a challenging technical or academic project you built.",
        "tip": "Use the STAR method: Situation, Task, Action, and Result."
    },
    {
        "question": "How do you prioritize deadlines when juggling multiple coursework assignments or job projects?",
        "tip": "Mention milestone planning, breaking down large requirements, and clear communication with project leads."
    }
]


def generate_interview_prep(skills: list[str]) -> list[dict[str, str]]:
    questions: list[dict[str, str]] = []
    seen = set()

    for s in skills:
        clean_s = s.strip().lower()
        if clean_s in SKILL_QUESTIONS:
            for item in SKILL_QUESTIONS[clean_s]:
                if item["question"] not in seen:
                    questions.append(item)
                    seen.add(item["question"])

    for gen in GENERAL_QUESTIONS:
        if gen["question"] not in seen and len(questions) < 5:
            questions.append(gen)
            seen.add(gen["question"])

    return questions[:6]
