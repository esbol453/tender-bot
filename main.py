import logging
import requests
from bs4 import BeautifulSoup
from html import escape
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from datetime import datetime, timedelta

TOKEN = "7008967829:AAHIcif9vD-j1gxYPGbQ5X7UY-0s2W3dqnk"

# URL с фильтрами Госзакуп
GOSZAKUP_URL = (
    "https://goszakup.gov.kz/ru/search/lots?"
    "filter%5Bmethod%5D%5B%5D=3&"                 # Запрос ценовых предложений
    "filter%5Bstatus%5D%5B%5D=240&"                # Опубликован (прием ценовых предложений)
    "filter%5Bkato%5D=470000000&"                   # Мангистауская область
    "filter%5Bamount_to%5D=1000000"                 # Сумма до 1 000 000 тг
)

def parse_goszakup():
    tenders = []
    try:
        response = requests.get(GOSZAKUP_URL, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        rows = soup.select("table.table tbody tr")
        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 6:
                continue

            title = cols[1].get_text(strip=True)
            description = cols[2].get_text(strip=True)
            quantity = cols[3].get_text(strip=True)
            price = cols[4].get_text(strip=True)
            method = cols[5].get_text(strip=True)
            status = cols[6].get_text(strip=True) if len(cols) > 6 else ""

            # Фильтр, на всякий случай — но сайт уже фильтрует
            if "Мангистауская" not in description and "Мангистауская" not in title:
                continue
            if "Запрос ценовых предложений" not in method:
                continue
            if "Опубликован" not in status:
                continue

            tenders.append({
                "title": title,
                "description": description,
                "quantity": quantity,
                "price": price,
                "status": status
            })

    except Exception as e:
        tenders.append({"title": f"Ошибка при загрузке Госзакуп: {e}", "description": "", "quantity": "", "price": "", "status": ""})

    return tenders

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот мониторю Госзакупы по Мангистаускому региону.\n\n"
        "Команды:\n"
        "/goszakup — показать актуальные тендеры"
    )

async def goszakup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    tenders = parse_goszakup()

    if not tenders or (len(tenders) == 1 and "Ошибка" in tenders[0]["title"]):
        await context.bot.send_message(chat_id=chat_id, text="[Госзакуп] Новых тендеров нет.")
        return

    for t in tenders:
        msg = (
            f"🔹 <b>{escape(t['title'])}</b>\n"
            f"Описание: {escape(t['description'])}\n"
            f"Количество: {escape(t['quantity'])}\n"
            f"Сумма: {escape(t['price'])} тг\n"
            f"Статус: {escape(t['status'])}\n"
        )
        await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode="HTML")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("goszakup", goszakup_command))

    print("Бот запущен...")
    app.run_polling()
