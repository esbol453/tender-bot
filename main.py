import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Вставь сюда свой токен
TOKEN = "7008967829:AAHIcif9vD-j1gxYPGbQ5X7UY-0s2W3dqnk"

# Функция парсинга госзакупок с фильтрами
def parse_tenders():
    tenders = []
    base_url = "https://goszakup.gov.kz/ru/search/lots"
    params = {
        "filter[method][]": "3",  # Запрос ценовых предложений
        "filter[status][]": "240",  # Опубликован (прием ценовых предложений)
        "filter[kato]": "470000000",  # Мангистауская область
        "filter[amount_to]": "1000000",  # Сумма до 1 млн
        "filter[trade_type]": "Товар",  # Предмет закупки Товар
        "page": 1
    }

    while True:
        print(f"Парсим страницу {params['page']}...")
        response = requests.get(base_url, params=params)
        if response.status_code != 200:
            break
        soup = BeautifulSoup(response.text, "html.parser")
        rows = soup.select("table.table > tbody > tr")

        if not rows:
            break

        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 7:
                continue

            # Данные из столбцов
            lot_number = cols[0].get_text(strip=True)
            name_desc = cols[1].get_text(strip=True)
            quantity = cols[3].get_text(strip=True)
            amount = cols[4].get_text(strip=True)
            method = cols[5].get_text(strip=True)
            status = cols[6].get_text(strip=True)

            # Проверяем условия (если надо - можно детальнее)
            if method == "Запрос ценовых предложений" and "прием ценовых предложений" in status.lower():
                tender_text = (
                    f"🔹 {name_desc}\n"
                    f"Количество: {quantity}\n"
                    f"Сумма: {amount} тг\n"
                    f"Статус: {status}\n"
                )
                tenders.append(tender_text)

        # Проверка на следующую страницу
        next_button = soup.select_one("ul.pagination > li.page-item.next:not(.disabled)")
        if next_button:
            params["page"] += 1
        else:
            break

    return tenders

# Команда /goszakup для бота
async def goszakup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ищу тендеры...")

    tenders = parse_tenders()
    if not tenders:
        await update.message.reply_text("[Госзакуп] Новых тендеров нет.")
    else:
        for tender in tenders:
            await update.message.reply_text(tender)

# Запуск бота
if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("goszakup", goszakup))
    print("Бот запущен...")
    app.run_polling()
