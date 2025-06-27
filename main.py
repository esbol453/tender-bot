import logging
from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

TOKEN = "7008967829:AAHIcif9vD-j1gxYPGbQ5X7UY-0s2W3dqnk"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот для мониторинга тендеров.\n"
        "Чтобы начать мониторинг, напишите /monitor"
    )

async def monitor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Мониторинг включен (пока пример).")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app: Application = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("monitor", monitor))

    app.run_polling()
