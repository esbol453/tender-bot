from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import requests
from bs4 import BeautifulSoup

TOKEN = "твой_токен"

BASE_URL = "https://goszakup.gov.kz/ru/search/lots"
FILTERS = {
    "filter[method][]": "3",
    "filter[status][]": "240",
    "filter[kato]": "470000000",
    "filter[amount_to]": "1000000",
    "page": 1
}

def fetch_page(page_num):
    params = FILTERS.copy()
    params["page"] = page_num
    response = requests.get(BASE_URL, params=params)
    if response.status_code != 200:
        return None
    return response.text

def parse_lots(html):
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.select("table.table > tbody > tr")
    lots = []
    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 7:
            continue

        lot_number = cells[0].get_text(strip=True)
        announcement = cells[1].get_text(" ", strip=True)
        lot_name_and_desc = cells[2].get_text(" ", strip=True)
        quantity = cells[3].get_text(strip=True)
        amount = cells[4].get_text(strip=True)
        purchase_method = cells[5].get_text(strip=True)
        status = cells[6].get_text(strip=True)

        lots.append({
            "lot_number": lot_number,
            "announcement": announcement,
            "lot_name_and_desc": lot_name_and_desc,
            "quantity": quantity,
            "amount": amount,
            "purchase_method": purchase_method,
            "status": status
        })
    return lots

async def goszakup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ищу тендеры...")
    all_lots = []
    for page in range(1, 8):
        html = fetch_page(page)
        if not html:
            break
        lots = parse_lots(html)
        if not lots:
            break
        all_lots.extend(lots)

    if not all_lots:
        await update.message.reply_text("[Госзакуп] Новых тендеров нет.")
        return

    for lot in all_lots:
        text = (
            f"🔹 {lot['lot_number']}\n"
            f"Объявление: {lot['announcement']}\n"
            f"Лот: {lot['lot_name_and_desc']}\n"
            f"Количество: {lot['quantity']}\n"
            f"Сумма: {lot['amount']} тг\n"
            f"Способ закупки: {lot['purchase_method']}\n"
            f"Статус: {lot['status']}\n"
        )
        await update.message.reply_text(text)

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("goszakup", goszakup_command))
    print("Бот запущен...")
    app.run_polling()
