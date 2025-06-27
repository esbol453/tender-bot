import logging
import requests
from bs4 import BeautifulSoup
from html import escape
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from datetime import datetime, timedelta

TOKEN = "7008967829:AAHIcif9vD-j1gxYPGbQ5X7UY-0s2W3dqnk"


# --- Госзакуп ---
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
                price_text = cols[4].text.strip().replace(" ", "").replace("\xa0", "")
                date_text = cols[3].text.strip()
                link = "https://goszakup.gov.kz" + cols[1].find("a")["href"]

                try:
                    price_value = float(price_text.replace("тг", "").replace(",", ".").strip())
                except:
                    price_value = 0

                try:
                    tender_date = datetime.strptime(date_text, "%d.%m.%Y")
                except:
                    tender_date = None

                if tender_date and tender_date < datetime.now() - timedelta(days=5):
                    continue

                lot_resp = requests.get(link, timeout=10)
                lot_resp.encoding = 'utf-8'
                lot_soup = BeautifulSoup(lot_resp.text, "html.parser")
                lot_text = lot_soup.get_text(separator="\n", strip=True)

                # --- Печатаем в консоль ---
                print("===")
                print("Ссылка:", link)
                print("Текст лота:")
                print(lot_text)
                print("===")

                if (
                    "Место поставки: Мангистауская область" in lot_text and
                    price_value <= 1_000_000 and
                    ("Товар" in lot_text or "Товары" in lot_text or "товар" in lot_text)
                ):
                    tenders.append({
                        "title": title,
                        "price": price_text,
                        "date": date_text,
                        "url": link
                    })

    except Exception as e:
        tenders.append({"title": f"Ошибка при загрузке Госзакуп: {e}", "price": "", "date": "", "url": ""})
    return tenders


# --- Самрук-Казына ---
def parse_samruk():
    return []


# --- /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Тестовый бот.\n\n"
        "/goszakup — показать тестовые данные."
    )


# --- /goszakup ---
async def goszakup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    tenders = parse_goszakup()
    await send_tenders(chat_id, tenders, "Госзакуп", context.bot)


# --- Отправка сообщений ---
async def send_tenders(chat_id, tenders, site_name, bot):
    if not tenders:
        await bot.send_message(chat_id=chat_id, text=f"[{site_name}] Новых тендеров нет.")
    else:
        for t in tenders:
            safe_title = escape(t["title"])
            safe_url = t["url"]
            msg = (
                f"🔹 [{site_name}] <b>{safe_title}</b>\n"
                f"💰 {t['price']}\n"
                f"📅 {t['date']}\n"
                f"🔗 <a href='{safe_url}'>Подробнее</a>"
            )
            await bot.send_message(chat_id=chat_id, text=msg, parse_mode="HTML")


# --- Запуск ---
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("goszakup", goszakup_command))

    app.run_polling()
