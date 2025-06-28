import logging
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "7008967829:AAHIcif9vD-j1gxYPGbQ5X7UY-0s2W3dqnk"

logging.basicConfig(level=logging.INFO)

def parse_goszakup():
    url = "https://goszakup.gov.kz/ru/announcements"
    tenders = []
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        rows = soup.select("table.table tbody tr")[:20]
        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 7:
                continue
            lot_name = cols[1].text.strip()
            lot_desc = cols[2].text.strip()
            quantity = cols[3].text.strip()
            price = cols[4].text.strip()
            method = cols[5].text.strip()
            status = cols[6].text.strip()
            tenders.append({
                "name": lot_name,
                "desc": lot_desc,
                "quantity": quantity,
                "price": price,
                "method": method,
                "status": status,
            })
    except Exception as e:
        tenders.append({"name": f"Ошибка при загрузке: {e}"})
    return tenders

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь /goszakup чтобы получить тендеры.")

async def goszakup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tenders = parse_goszakup()
    if not tenders:
        await update.message.reply_text("[Госзакуп] Новых тендеров нет.")
    else:
        for t in tenders:
            msg = (
                f"🔹 {t.get('name', '')}\n"
                f"Описание: {t.get('desc', '')}\n"
                f"Количество: {t.get('quantity', '')}\n"
                f"Цена: {t.get('price', '')}\n"
                f"Способ закупки: {t.get('method', '')}\n"
                f"Статус: {t.get('status', '')}\n"
                "-------------------------"
            )
            await update.message.reply_text(msg)

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("goszakup", goszakup_command))
    app.run_polling()
