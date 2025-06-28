import logging
import requests
from bs4 import BeautifulSoup
from html import escape
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = "7008967829:AAHIcif9vD-j1gxYPGbQ5X7UY-0s2W3dqnk"

logging.basicConfig(level=logging.INFO)

def parse_goszakup():
    url = "https://goszakup.gov.kz/ru/announcements"
    tenders = []
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        rows = soup.select("table.table tbody tr")
        logging.info(f"Нашли строк таблицы: {len(rows)}")

        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 7:
                continue
            name_html = cols[1].find("a")
            name = name_html.get_text(strip=True) if name_html else cols[1].get_text(strip=True)
            desc_html = cols[2].find("a")
            desc = desc_html.get_text(strip=True) if desc_html else cols[2].get_text(strip=True)
            quantity = cols[3].get_text(strip=True)
            price = cols[4].get_text(strip=True)
            purchase_method = cols[5].get_text(strip=True)
            status = cols[6].get_text(strip=True)
            # Для места поставки попытаемся найти в описании или в другом месте — здесь нет отдельной колонки, но можно искать по тексту:
            place = ""
            # Можно взять из описания, если там есть Мангистауская
            if "Мангистауская" in desc:
                place = "Мангистауская область"
            else:
                place = "Не указано"

            link = "https://goszakup.gov.kz" + (name_html['href'] if name_html else "")

            tenders.append({
                "name": name,
                "desc": desc,
                "quantity": quantity,
                "price": price,
                "purchase_method": purchase_method,
                "status": status,
                "place": place,
                "url": link
            })

    except Exception as e:
        logging.error(f"Ошибка парсинга Госзакуп: {e}")
    return tenders

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот для мониторинга тендеров.\n\n"
        "Команды:\n"
        "/goszakup — показать тендеры с Госзакуп"
    )

async def goszakup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    tenders = parse_goszakup()
    if not tenders:
        await update.message.reply_text("[Госзакуп] Новых тендеров нет.")
        return

    await update.message.reply_text(f"[Госзакуп] Найдено тендеров: {len(tenders)}")

    for tender in tenders[:10]:  # ограничим 10 сообщениями, чтобы не спамить
        msg = (
            f"🏷 <b>{escape(tender['name'])}</b>\n"
            f"📄 {escape(tender['desc'])}\n"
            f"📦 Кол-во: {escape(tender['quantity'])}\n"
            f"💰 Сумма: {escape(tender['price'])}\n"
            f"⚙ Способ закупки: {escape(tender['purchase_method'])}\n"
            f"📍 Место поставки: {escape(tender['place'])}\n"
            f"🟢 Статус: {escape(tender['status'])}\n"
            f"🔗 <a href='{tender['url']}'>Подробнее</a>"
        )
        await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode="HTML", disable_web_page_preview=True)

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("goszakup", goszakup_command))
    app.run_polling()
