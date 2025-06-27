import logging
import requests
from bs4 import BeautifulSoup
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
            if len(cols) >= 5:
                title = cols[1].text.strip()
                price_text = cols[4].text.strip().replace(" ", "").replace(" ", "")
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

                if (
                    ("Мангистауская" in title or "Мангистауская" in cols[2].text)
                    and ("Запрос ценовых предложений" in title)
                    and (price_value <= 1_000_000)
                    and ("Товар" in title or "Товары" in title)
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
    url = "https://zakup.sk.kz/api/tenders"
    tenders = []
    try:
        response = requests.get(url, timeout=10)
        if not response.headers.get("Content-Type", "").startswith("application/json"):
            raise ValueError("API не вернул JSON. Возможно, требуется авторизация.")
        data = response.json()
        for tender in data.get("data", []):
            title = tender.get("title", "")
            region = tender.get("region", "")
            price = tender.get("price", "0")
            procedure = tender.get("procedure", "")
            category = tender.get("category", "")
            date_text = tender.get("date", "-")

            price_value = 0
            try:
                price_value = float(str(price).replace(" ", "").replace(",", "."))
            except:
                pass

            # Фильтр по дате
            tender_date = None
            try:
                tender_date = datetime.strptime(date_text, "%d.%m.%Y")
            except:
                pass

            if tender_date and tender_date < datetime.now() - timedelta(days=5):
                continue

            if (
                "Мангистауская" in region
                and "Запрос ценовых предложений" in procedure
                and "Товар" in category
                and price_value <= 1_000_000
            ):
                tenders.append({
                    "title": title,
                    "price": price,
                    "date": date_text,
                    "url": tender.get("url", "https://zakup.sk.kz")
                })
    except Exception as e:
        tenders.append({"title": f"Ошибка при загрузке Самрук: {e}", "price": "", "date": "", "url": ""})
    return tenders


# --- /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот для мониторинга тендеров.\n\n"
        "Регион: Мангистауская область\n"
        "Категория: Товары\n"
        "Тип: Запрос ценовых предложений\n"
        "Сумма: до 1 000 000 тг\n\n"
        "Команды:\n"
        "/monitor — выбрать источник\n"
        "/goszakup — показать с Госзакуп\n"
        "/samruk — показать с Самрук-Казына"
    )


# --- /monitor: кнопки ---
async def monitor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("Госзакуп", callback_data="goszakup"),
            InlineKeyboardButton("Самрук", callback_data="samruk"),
        ],
        [
            InlineKeyboardButton("Оба сайта", callback_data="both"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Выберите источник тендеров:",
        reply_markup=reply_markup
    )


# --- Обработка кнопок ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    choice = query.data
    chat_id = query.message.chat.id

    sources = []
    if choice == "goszakup":
        sources = [("Госзакуп", parse_goszakup)]
    elif choice == "samruk":
        sources = [("Самрук-Казына", parse_samruk)]
    elif choice == "both":
        sources = [("Госзакуп", parse_goszakup), ("Самрук-Казына", parse_samruk)]

    for site_name, parser in sources:
        tenders = parser()
        if not tenders:
            await context.bot.send_message(chat_id=chat_id, text=f"[{site_name}] Новых тендеров нет.")
        else:
            for t in tenders:
                msg = (
                    f"🔹 [{site_name}] <b>{t['title']}</b>\n"
                    f"💰 {t['price']}\n"
                    f"📅 {t['date']}\n"
                    f"🔗 <a href='{t['url']}'>Подробнее</a>"
                )
                await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode="HTML")


# --- Отдельные команды /goszakup и /samruk ---
async def goszakup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    tenders = parse_goszakup()
    if not tenders:
        await context.bot.send_message(chat_id=chat_id, text="Госзакуп: Новых тендеров нет.")
    else:
        for t in tenders:
            msg = (
                f"🔹 [Госзакуп] <b>{t['title']}</b>\n"
                f"💰 {t['price']}\n"
                f"📅 {t['date']}\n"
                f"🔗 <a href='{t['url']}'>Подробнее</a>"
            )
            await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode="HTML")


async def samruk_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    tenders = parse_samruk()
    if not tenders:
        await context.bot.send_message(chat_id=chat_id, text="Самрук-Казына: Новых тендеров нет.")
    else:
        for t in tenders:
            msg = (
                f"🔹 [Самрук-Казына] <b>{t['title']}</b>\n"
                f"💰 {t['price']}\n"
                f"📅 {t['date']}\n"
                f"🔗 <a href='{t['url']}'>Подробнее</a>"
            )
            await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode="HTML")


# --- Запуск приложения ---
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("monitor", monitor))
    app.add_handler(CommandHandler("goszakup", goszakup_command))
    app.add_handler(CommandHandler("samruk", samruk_command))
    app.add_handler(CallbackQueryHandler(button_handler))

    app.run_polling()
