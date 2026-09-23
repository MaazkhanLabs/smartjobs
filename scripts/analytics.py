import json

from app.database import SessionLocal
from app.services.analytics import get_analytics


def main():
    db = SessionLocal()

    try:
        print(
            json.dumps(
                get_analytics(db),
                indent=2,
            )
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
