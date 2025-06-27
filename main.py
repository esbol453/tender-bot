import logging
import requests
from bs4 import BeautifulSoup
from html import escape
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)
from datetime import datetime, timedelta

TOKEN = "7008967829:AAHIcif9vD-j1gxYPGbQ5X7UY-0s2W3dqnk"

def parse_goszakup():
    url = "https://goszakup.gov.kz/ru/announcements"
    tenders = []
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        rows = soup.select("table.table tbody tr")[:10]
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 5:
                title = cols[1].text.strip()
                date_text = cols[3].text.strip()
                link = "https://goszakup.gov.kz" + cols[1].find("a")["href"]

                try:
                    tender_date = datetime.strptime(date_text, "%d.%m.%Y")
                except:
                    tender_date = None

                if tender_date and tender_date < datetime.now() - timedelta(days=15):
                    continue

                tenders.append({
                    "title": title,
                    "date": date_text,
                    "url": link
                })

    except Exception as e:
        tenders.append({"title": f"Ошибка при загрузке: {e}", "date": "", "url": ""})
    return tenders


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Бот запущен.\n\nКоманда:\n/goszakup — получить последние объявления без фильтра."
    )


async def goszakup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    tenders = parse_goszakup()
    await send_tenders(chat_id, tenders, context.bot)


async def send_tenders(chat_id, tenders, bot):
    if not tenders:
        await bot.send_message(chat_id=chat_id, text="[Госзакуп] Новых тендеров нет.")
    else:
        for t in tenders:
            safe_title = escape(t["title"])
            safe_url = t["url"]
            msg = (
                f"🔹 <b>{safe_title}</b>\n"
                f"📅 {t['date']}\n"
                f"🔗 <a href='{safe_url}'>Подробнее</a>"
            )
            await bot.send_message(chat_id=chat_id, text=msg, parse_mode="HTML")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("goszakup", goszakup_command))
    app.run_polling()
