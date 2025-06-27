
import logging
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, JobQueue

TOKEN = "7008967829:AAHIcif9vD-j1gxYPGbQ5X7UY-0s2W3dqnk"

# --- Госзакуп (HTML парсинг) с фильтрацией ---
def parse_goszakup():
    url = "https://goszakup.gov.kz/ru/announcements"
    tenders = []
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        rows = soup.select("table.table tbody tr")[:10]  # проверяем больше строк
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
                # Фильтрация
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
        tenders.append({"title": f"Ошибка при загрузке Госзакуп: {e}", "price": "", "date": "", "url": ""})
    return tenders

# --- Самрук-Казына (API) с фильтрацией ---
def parse_samruk():
    url = "https://zakup.sk.kz/api/tenders"
    tenders = []
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        for tender in data.get("data", []):
            title = tender.get("title", "")
            region = tender.get("region", "")
            price = tender.get("price", "0")
            procedure = tender.get("procedure", "")
            category = tender.get("category", "")
            # Фильтрация
            price_value = 0
            try:
                price_value = float(str(price).replace(" ", "").replace(",", "."))
            except:
                pass
            if (
                "Мангистауская" in region
                and "Запрос ценовых предложений" in procedure
                and "Товар" in category
                and price_value <= 1000000
            ):
                tenders.append({
                    "title": title,
                    "price": price,
                    "date": tender.get("date", "-"),
                    "url": tender.get("url", "https://zakup.sk.kz")
                })
    except Exception as e:
        tenders.append({"title": f"Ошибка при загрузке Самрук-Казына: {e}", "price": "", "date": "", "url": ""})
    return tenders

# --- Telegram команды ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот для мониторинга тендеров.
"
        "Регион: Мангистауская область
"
        "Категория: Товары
"
        "Тип: Запрос ценовых предложений
"
        "Сумма: до 1 000 000 тг
"
        "Команда: /monitor"
    )

async def check_tenders(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id

    for site_name, parser in [("Госзакуп", parse_goszakup), ("Самрук-Казына", parse_samruk)]:
        tenders = parser()
        if not tenders:
            await context.bot.send_message(chat_id=chat_id, text=f"[{site_name}] Новых тендеров нет.")
        for t in tenders:
            msg = (
                f"🔹 [{site_name}] <b>{t['title']}</b>
"
                f"💰 {t['price']}
"
                f"📅 {t['date']}
"
                f"🔗 <a href='{t['url']}'>Подробнее</a>"
            )
            await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode="HTML")

async def enable_monitoring(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    job_queue: JobQueue = context.job_queue
    job_queue.run_repeating(check_tenders, interval=3600, first=5, chat_id=chat_id)
    await update.message.reply_text("Мониторинг включен. Я буду присылать тендеры каждый час.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("monitor", enable_monitoring))
    app.run_polling()
