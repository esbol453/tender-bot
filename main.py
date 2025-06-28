import requests
from bs4 import BeautifulSoup

def parse_goszakup_filtered_debug(max_pages=3):
    base_url = "https://goszakup.gov.kz/ru/search/lots"
    tenders = []

    for page in range(1, max_pages + 1):
        params = {
            "filter[method][]": "3",       # Запрос ценовых предложений
            "filter[status][]": "240",     # Опубликован (прием ценовых предложений)
            "filter[kato]": "470000000",   # Мангистауская область
            "filter[amount_to]": "1000000",
            "page": page
        }
        print(f"Парсим страницу {page}...")
        response = requests.get(base_url, params=params)
        if response.status_code != 200:
            print(f"Ошибка загрузки страницы {page}: статус {response.status_code}")
            break

        soup = BeautifulSoup(response.text, "html.parser")
        rows = soup.select("table.table tbody tr")
        if not rows:
            print("Лоты на странице не найдены, прерываем.")
            break

        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 7:
                continue

            title = cols[1].get_text(separator=" ", strip=True)
            description = cols[2].get_text(separator=" ", strip=True)
            quantity = cols[3].get_text(strip=True)
            price = cols[4].get_text(strip=True)
            method = cols[5].get_text(strip=True)
            status = cols[6].get_text(strip=True)

            print(f"Заголовок: {title}")
            print(f"Описание: {description}")
            print(f"Метод: {method}")
            print(f"Статус: {status}")
            print(f"Цена: {price}")
            print("---")

            # Добавляем все лоты без фильтра по "Товар" для отладки
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
    tenders = parse_goszakup_filtered_debug()
    if tenders:
        print(f"Всего лотов за 3 страницы: {len(tenders)}")
    else:
        print("[Госзакуп] Новых тендеров нет.")
