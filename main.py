import requests
from bs4 import BeautifulSoup

def parse_goszakup_filtered(max_pages=7):
    base_url = "https://goszakup.gov.kz/ru/search/lots"
    params = {
        "filter[method][]": "3",           # Запрос ценовых предложений
        "filter[status][]": "240",         # Опубликован (прием ценовых предложений)
        "filter[kato]": "470000000",       # Мангистауская область
        "filter[amount_to]": "1000000",    # до 1 000 000 тг
        "page": 1
    }
    tenders = []

    for page in range(1, max_pages + 1):
        params["page"] = page
        response = requests.get(base_url, params=params)
        soup = BeautifulSoup(response.text, "html.parser")
        rows = soup.select("table tbody tr")
        if not rows:
            break  # Если лоты на странице закончились

        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 7:
                continue

            title = cols[1].text.strip()
            description = cols[2].text.strip()
            quantity = cols[3].text.strip()
            price = cols[4].text.strip()
            method = cols[5].text.strip()
            status = cols[6].text.strip()

            # Проверяем фильтры
            if "Товар" not in title and "Товар" not in description:
                continue
            if method != "Запрос ценовых предложений":
                continue
            if status != "Опубликован (прием ценовых предложений)":
                continue

            # Дополнительно можно проверить цену (убрать пробелы, привести к числу)
            price_num = float(price.replace(" ", "").replace(",", "."))
            if price_num > 1000000:
                continue

            tenders.append({
                "title": title,
                "description": description,
                "quantity": quantity,
                "price": price,
                "method": method,
                "status": status,
            })

    return tenders


if __name__ == "__main__":
    all_tenders = parse_goszakup_filtered()
    if all_tenders:
        for t in all_tenders:
            print(f"🔹 {t['title']}\nОписание: {t['description']}\nКоличество: {t['quantity']}\nСумма: {t['price']} тг\nСтатус: {t['status']}\n")
    else:
        print("[Госзакуп] Новых тендеров нет.")
