import logging
import requests
from bs4 import BeautifulSoup
from html import escape
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from datetime import datetime, timedelta

TOKEN = "7008967829:AAHIcif9vD-j1gxYPGbQ5X7UY-0s2W3dqnk"

BASE_URL = (
    "https://goszakup.gov.kz/ru/search/lots?"
    "filter%5Bmethod%5D%5B%5D=3&"
    "filter%5Bstatus%5D%5B%5D=240&"
    "filter%5Bkato%5D=470000000&"
    "filter%5Bamount_to%5D=1000000&page="
)

DAYS_BACK = 5

def parse_goszakup():
    tenders = []
    now = datetime.now()

    for page in range(1, 3):  # первые 2 страницы
        url = BASE_URL + str(page)
        try:
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

                link_tag = cols[1].find("a")
                if not link_tag:
                    continue

                title = link_tag.get_text(strip=True)
                link = "https://goszakup.gov.kz" + link_tag.get("href", "")

                date_created = None
                tooltip = link_tag.get("title", "")
                if "Создано:" in tooltip:
                    date_str = tooltip.split("Создано:")[-1].strip().split(" ")[0]
                    date_created = datetime.strptime(date_str, "%d.%m.%Y")
                    if (now - date_created).days > DAYS_BACK:
                        continue

                description = cols[2].get_text(strip=True)
                quantity = cols[3].get_text(strip=True)
                price = cols[4].get_text(strip=True)
                method = cols[5].get_text(strip=True)
                status = cols[6].get_text(strip=True)

                tenders.append({
                    "title": title,
                    "link": link,
                    "description": description,
                    "quantity": quantity,
                    "price": price,
                    "status": status
                })

        except Exception as e:
            tenders.append({
                "title": f"Ошибка при загрузке Госзакуп: {e}",
                "link": "",
                "description": "",
                "quantity": "",
                "price": "",
                "status": ""
            })
            break

    return tenders

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот мониторю Госзакупы по Мангистаускому региону.\n\n"
        "Команда:\n"
        "/goszakup — показать актуальные тендеры за последние 5 дней."
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
            f"<a href='{escape(t['link'])}'>Ссылка на лот</a>\n"
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
