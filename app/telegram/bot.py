from __future__ import annotations
import secrets

from sqlalchemy import select

from app.config import settings
from app.database import SessionLocal
from app.models import User, Recommendation, Job

try:
    from telegram import Update
    from telegram.ext import (
        Application,
        CommandHandler,
        ContextTypes,
    )
except (ImportError, Exception):
    Update = None
    Application = None
    CommandHandler = None
    ContextTypes = None


# In production, persist these tokens in a database table with expiry.
LINK_TOKENS: dict[str, int] = {}


def create_link_token(user_id: int) -> str:
    token = secrets.token_urlsafe(12)
    LINK_TOKENS[token] = user_id
    return token


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or not update.message:
        return

    args = context.args

    db = SessionLocal()

    try:
        if args:
            token = args[0]
            user_id = LINK_TOKENS.pop(token, None)

            if user_id:
                user = db.get(User, user_id)
                if user:
                    user.telegram_user_id = str(
                        update.effective_user.id
                    )
                    db.commit()

                    await update.message.reply_text(
                        "Telegram account linked successfully."
                    )
                    return

        await update.message.reply_text(
            "Welcome to Smart Internship Aggregator!\n\n"
            "Link your account from the web profile page, then use /jobs."
        )
    finally:
        db.close()


async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or not update.message:
        return

    telegram_id = str(update.effective_user.id)

    db = SessionLocal()

    try:
        user = db.scalar(
            select(User).where(
                User.telegram_user_id == telegram_id
            )
        )

        if not user:
            await update.message.reply_text(
                "Your Telegram account is not linked yet."
            )
            return

        skills = ", ".join(skill.skill for skill in user.skills)

        await update.message.reply_text(
            f"Name: {user.name}\n"
            f"Branch: {user.branch or '-'}\n"
            f"Year: {user.year or '-'}\n"
            f"CGPA: {user.cgpa or '-'}\n"
            f"Skills: {skills or '-'}"
        )
    finally:
        db.close()


async def jobs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or not update.message:
        return

    telegram_id = str(update.effective_user.id)

    db = SessionLocal()

    try:
        user = db.scalar(
            select(User).where(
                User.telegram_user_id == telegram_id
            )
        )

        if not user:
            await update.message.reply_text(
                "Link your Telegram account first."
            )
            return

        rows = db.execute(
            select(Recommendation, Job)
            .join(Job, Recommendation.job_id == Job.id)
            .where(
                Recommendation.user_id == user.id,
                Job.is_active.is_(True),
            )
            .order_by(Recommendation.score.desc())
            .limit(5)
        ).all()

        if not rows:
            await update.message.reply_text(
                "No recommendations yet. Complete your profile first."
            )
            return

        messages = []

        for index, (rec, job) in enumerate(rows, start=1):
            messages.append(
                f"{index}. {job.title} — {job.company}\n"
                f"Score: {rec.score:.2f}\n"
                f"{job.location} | {job.work_mode}\n"
                f"Apply: {job.apply_url}"
            )

        await update.message.reply_text(
            "\n\n".join(messages)
        )
    finally:
        db.close()


async def alerts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or not update.message:
        return

    telegram_id = str(update.effective_user.id)

    if not context.args or context.args[0].lower() not in {"on", "off"}:
        await update.message.reply_text(
            "Usage: /alerts on OR /alerts off"
        )
        return

    enabled = context.args[0].lower() == "on"

    db = SessionLocal()

    try:
        user = db.scalar(
            select(User).where(
                User.telegram_user_id == telegram_id
            )
        )

        if not user:
            await update.message.reply_text(
                "Link your account first."
            )
            return

        user.telegram_alerts_enabled = enabled
        db.commit()

        await update.message.reply_text(
            "Daily alerts enabled." if enabled
            else "Daily alerts disabled."
        )
    finally:
        db.close()


async def send_daily_digest(context: ContextTypes.DEFAULT_TYPE):
    db = SessionLocal()

    try:
        users = db.scalars(
            select(User).where(
                User.telegram_alerts_enabled.is_(True),
                User.telegram_user_id.is_not(None),
            )
        ).all()

        for user in users:
            if not user.telegram_user_id:
                continue

            rows = db.execute(
                select(Recommendation, Job)
                .join(Job, Recommendation.job_id == Job.id)
                .where(
                    Recommendation.user_id == user.id,
                    Job.is_active.is_(True),
                )
                .order_by(Recommendation.score.desc())
                .limit(5)
            ).all()

            if not rows:
                continue

            text = "🎯 Your top internship/job matches today:\n\n"

            for i, (rec, job) in enumerate(rows, start=1):
                text += (
                    f"{i}. {job.title} — {job.company}\n"
                    f"Match: {rec.score:.0%}\n"
                    f"{job.location} | {job.work_mode}\n"
                    f"{job.apply_url}\n\n"
                )

            try:
                await context.bot.send_message(
                    chat_id=int(user.telegram_user_id),
                    text=text,
                )
            except Exception as exc:
                print(
                    f"Telegram delivery failed for user {user.id}: {exc}"
                )
    finally:
        db.close()


def build_application():
    if not settings.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured.")

    application = Application.builder().token(
        settings.telegram_bot_token
    ).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("profile", profile))
    application.add_handler(CommandHandler("jobs", jobs))
    application.add_handler(CommandHandler("alerts", alerts))

    # 24-hour digest.
    if application.job_queue:
        application.job_queue.run_repeating(
            send_daily_digest,
            interval=24 * 60 * 60,
            first=30,
        )

    return application


def run_bot():
    application = build_application()
    application.run_polling()
