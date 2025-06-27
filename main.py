import logging
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

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
                price_text = cols[4].text.strip().replace(" ", "").replace(" ", "")
                date = cols[3].text.strip()
                link = "https://goszakup.gov.kz" + cols[1].find("a")["href"]
                try:
                    price_value = float(price_text.replace("тг", "").replace(",", ".").strip())
                except:
                    price_value = 0
                if (
                    "Мангистауская" in title or "Мангистауская" in cols[2].text
                ) and (
                    "Запрос ценовых предложений" in title
                ) and (
                    price_value <= 1000000
                ) and (
                    "Товар" in title or "Товары" in title
                ):
                    tenders.append({
                        "title": title,
                        "price": price_text,
                        "date": date,
                        "url": link
                    })
    except Exception as e:
        tenders.append({"title": f"Ошибка при загрузке: {e}", "price": "", "date": "", "url": ""})
    return tenders


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот для мониторинга тендеров.\n"
        "Регион: Мангистауская область\n"
        "Категория: Товары\n"
        "Тип: Запрос ценовых предложений\n"
        "Сумма: до 1 000 000 тг\n"
        "Команда: /monitor"
    )


async def monitor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tenders = parse_goszakup()
    if not tenders:
        await update.message.reply_text("Новых тендеров нет.")
    for t in tenders:
        msg = (
            f"🔹 <b>{t['title']}</b>\n"
            f"💰 {t['price']}\n"
            f"📅 {t['date']}\n"
            f"🔗 <a href='{t['url']}'>Подробнее</a>"
        )
        await update.message.reply_text(msg, parse_mode="HTML")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("monitor", monitor))
    application.run_polling()
