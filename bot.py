import json
import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo

from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

from apscheduler.schedulers.asyncio import AsyncIOScheduler

TOKEN = "YOUR_BOT_TOKEN"

bot = Bot(token=TOKEN)

SCHEDULE_FILE = "schedule.json"
CHATS_FILE = "chats.json"


def load_json(file):
    try:
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_chats():
    data = load_json(CHATS_FILE)
    return data if isinstance(data, list) else []


def save_chats(chats):
    save_json(CHATS_FILE, chats)


def load_schedule():
    data = load_json(SCHEDULE_FILE)
    return data if isinstance(data, dict) else {}


async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.effective_chat.id

    chats = load_chats()

    if chat_id not in chats:
        chats.append(chat_id)
        save_chats(chats)

    await update.message.reply_text("Бот подключен к расписанию")


async def send_schedule():

    schedule = load_schedule()

    now = datetime.now(ZoneInfo("Asia/Dushanbe"))

    day = now.strftime("%A")

    if day == "Sunday":
        return

    text = f"📚 Расписание на {day}\n\n"

    if day in schedule:

        for lesson in schedule[day]:

            text += (
                f"{lesson['time']}\n"
                f"{lesson['subject']}\n"
                f"Аудитория: {lesson['room']}\n\n"
            )

    chats = load_chats()

    for chat in chats:

        try:
            await bot.send_message(chat, text)
        except:
            pass


async def broadcast(text):

    chats = load_chats()

    for chat in chats:

        try:
            await bot.send_message(chat, text)
        except:
            pass


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await register(update, context)


async def message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await register(update, context)


def start_scheduler():

    scheduler = AsyncIOScheduler(timezone="Asia/Dushanbe")

    scheduler.add_job(send_schedule, "cron", hour=6, minute=0)

    scheduler.start()


async def main():

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.ALL, message))

    start_scheduler()

    print("Bot started")

    await app.run_polling()


if __name__ == "__main__":

    asyncio.run(main())
