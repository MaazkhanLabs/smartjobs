from app.database import SessionLocal
from app.services.recommendations import recompute_for_all_users


def main():
    db = SessionLocal()

    try:
        recompute_for_all_users(db)
        print("Recommendations recomputed for all users.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
