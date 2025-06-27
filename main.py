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
        rows = soup.select("table.table tbody tr")[:20]
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 7:
                title = cols[1].text.strip()
                description = cols[2].text.strip()
                quantity = cols[3].text.strip()
                price_text = cols[4].text.strip().replace(" ", "").replace(" ", "")
                procedure = cols[5].text.strip()
                status = cols[6].text.strip()
                link = "https://goszakup.gov.kz" + cols[1].find("a")["href"]

                try:
                    price_value = float(price_text.replace("тг", "").replace(",", ".").strip())
                except:
                    price_value = 0

                # --- DEBUG вывод ---
                print("==== DEBUG ====")
                print(f"title: {title}")
                print(f"description: {description}")
                print(f"quantity: {quantity}")
                print(f"procedure: {procedure}")
                print(f"status: {status}")
                print(f"price_value: {price_value}")

                # Условие поиска
                if (
                    "Мангистауская" in description
                    and "Запрос ценовых предложений" in procedure
                    and "Опубликован (прием ценовых предложений)" in status
                    and price_value <= 1_000_000
                ):
                    tenders.append({
                        "title": title,
                        "description": description,
                        "quantity": quantity,
                        "price": price_text,
                        "status": status,
                        "url": link
                    })

    except Exception as e:
        tenders.append({"title": f"Ошибка при загрузке Госзакуп: {e}", "description": "", "quantity": "", "price": "", "status": "", "url": ""})
    return tenders


# --- Самрук-Казына ---
def parse_samruk():
    return []  # Оставим пустым, чтобы не мешало тестировать Госзакуп


# --- /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот для мониторинга тендеров.\n\n"
        "Регион: Мангистауская область\n"
        "Категория: Товары\n"
        "Тип: Запрос ценовых предложений\n"
        "Сумма: до 1 000 000 тг\n\n"
        "Команды:\n"
        "/goszakup — показать с Госзакуп"
    )


# --- Отправка сообщений с экранированием ---
async def send_tenders(chat_id, tenders, site_name, bot):
    if not tenders:
        await bot.send_message(chat_id=chat_id, text=f"[{site_name}] Новых тендеров нет.")
    else:
        for t in tenders:
            safe_title = escape(t["title"])
            safe_description = escape(t["description"])
            msg = (
                f"🔹 [{site_name}] <b>{safe_title}</b>\n"
                f"📄 {safe_description}\n"
                f"🔢 Кол-во: {t['quantity']}\n"
                f"💰 {t['price']}\n"
                f"📍 Статус: {t['status']}\n"
                f"🔗 <a href='{t['url']}'>Подробнее</a>"
            )
            await bot.send_message(chat_id=chat_id, text=msg, parse_mode="HTML")


# --- /goszakup команда ---
async def goszakup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    tenders = parse_goszakup()
    await send_tenders(chat_id, tenders, "Госзакуп", context.bot)


# --- Запуск приложения ---
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("goszakup", goszakup_command))

    app.run_polling()
