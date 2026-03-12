import json
import os
import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import FastAPI
import uvicorn

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    CommandHandler,
    filters
)

TOKEN = os.getenv("BOT_TOKEN")

SCHEDULE_FILE = "schedule.json"
CHATS_FILE = "chats.json"

api = FastAPI()


def load_json(file):

    try:
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def save_json(file, data):

    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_schedule():

    data = load_json(SCHEDULE_FILE)

    if isinstance(data, dict):
        return data

    return {}


def load_chats():

    data = load_json(CHATS_FILE)

    if isinstance(data, list):
        return data

    return []


def save_chats(chats):

    save_json(CHATS_FILE, chats)


# регистрация чатов

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.effective_chat.id

    chats = load_chats()

    if chat_id not in chats:

        chats.append(chat_id)

        save_chats(chats)

    await update.message.reply_text("Бот подключен к расписанию")


# отправка расписания

async def send_schedule(context: ContextTypes.DEFAULT_TYPE):

    schedule = load_schedule()

    now = datetime.now(ZoneInfo("Asia/Dushanbe"))

    day = now.strftime("%A")

    if day == "Sunday":
        return

    text = f"📚 Расписание на {day}\n\n"

    if day in schedule:

        for i, lesson in enumerate(schedule[day], start=1):

            text += (
                f"{i}. {lesson['time']}\n"
                f"{lesson['subject']}\n"
                f"🏫 {lesson['room']}\n\n"
            )

    chats = load_chats()

    for chat in chats:

        try:

            await context.bot.send_message(chat, text)

        except:

            pass


# команда показать сегодня

async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await send_schedule(context)


# API добавления урока

@api.post("/add_lesson")

async def add_lesson(data: dict):

    schedule = load_schedule()

    day = data["day"]

    if day not in schedule:
        schedule[day] = []

    schedule[day].append({

        "time": data["time"],
        "subject": data["subject"],
        "room": data["room"]

    })

    save_json(SCHEDULE_FILE, schedule)

    return {"status": "lesson added"}


# API удаления урока

@api.post("/delete_lesson")

async def delete_lesson(data: dict):

    schedule = load_schedule()

    day = data["day"]

    index = data["index"]

    if day in schedule and len(schedule[day]) > index:

        schedule[day].pop(index)

    save_json(SCHEDULE_FILE, schedule)

    return {"status": "lesson deleted"}


# API рассылки

@api.post("/broadcast")

async def broadcast(data: dict):

    chats = load_chats()

    from telegram import Bot

    bot = Bot(TOKEN)

    for chat in chats:

        try:

            await bot.send_message(chat, data["text"])

        except:

            pass

    return {"status": "sent"}


# запуск API

def start_api():

    uvicorn.run(api, host="0.0.0.0", port=8000)


async def main():

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", register))

    app.add_handler(CommandHandler("today", today))

    app.add_handler(MessageHandler(filters.ALL, register))

    scheduler = AsyncIOScheduler(timezone="Asia/Dushanbe")

    scheduler.add_job(send_schedule, "cron", hour=6, minute=0)

    scheduler.start()

    print("BOT STARTED")

    await app.run_polling()


if __name__ == "__main__":

    import threading

    threading.Thread(target=start_api).start()

    asyncio.run(main())
