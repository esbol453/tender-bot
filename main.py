import logging
import requests
from bs4 import BeautifulSoup
from html import escape
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "7008967829:AAHIcif9vD-j1gxYPGbQ5X7UY-0s2W3dqnk"

BASE_URL = (
    "https://goszakup.gov.kz/ru/search/lots?"
    "filter%5Bmethod%5D%5B%5D=3&"
    "filter%5Bstatus%5D%5B%5D=240&"
    "filter%5Bkato%5D=470000000&"
    "filter%5Bamount_to%5D=1000000"
)

def parse_all_pages():
    tenders = []
    for page in range(1, 10):  # Можешь увеличить до 10-20, если нужно
        url = f"{BASE_URL}&page={page}"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        rows = soup.select("table.table tbody tr")
        if not rows:
            break

        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 7:
                continue

            lot_number = cols[0].get_text(strip=True)
            name = cols[1].find("strong").get_text(strip=True)
            customer_tag = cols[1].find("small")
            customer = customer_tag.get_text(strip=True).replace("Заказчик:", "").strip() if customer_tag else ""
            description = cols[2].find("strong").get_text(strip=True)
            quantity = cols[3].get_text(strip=True)
            price = cols[4].get_text(strip=True)
            method = cols[5].get_text(strip=True)
            status = cols[6].get_text(strip=True)

            tenders.append({
                "lot_number": lot_number,
                "name": name,
                "description": description,
                "customer": customer,
                "quantity": quantity,
                "price": price,
                "method": method,
                "status": status,
            })
    return tenders

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот, мониторящий Госзакуп.\n\n"
        "Команда:\n"
        "/goszakup — показать актуальные тендеры."
    )

async def goszakup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    tenders = parse_all_pages()

    if not tenders:
        await context.bot.send_message(chat_id=chat_id, text="[Госзакуп] Новых тендеров нет.")
        return

    for t in tenders:
        text = (
            f"🔹 {escape(t['lot_number'])}\n"
            f"Наименование: {escape(t['name'])}\n"
            f"Описание: {escape(t['description'])}\n"
            f"Заказчик: {escape(t['customer'])}\n"
            f"Количество: {escape(t['quantity'])}\n"
            f"Сумма: {escape(t['price'])} тг\n"
            f"Статус: {escape(t['status'])}\n"
        )
        await context.bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("goszakup", goszakup))

    print("Бот запущен...")
    app.run_polling()
