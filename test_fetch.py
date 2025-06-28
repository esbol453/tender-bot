import requests
from bs4 import BeautifulSoup

BASE_URL = "https://goszakup.gov.kz/ru/search/lots"

def test_fetch():
    session = requests.Session()
    params = {
        "page": "1",
        "filter[method][]": "3",
        "filter[status][]": "240",
        "filter[kato]": "470000000",
        "filter[amount_to]": "1000000",
    }

    resp = session.get(BASE_URL, params=params, timeout=15)
    resp.raise_for_status()
    html = resp.text

    soup = BeautifulSoup(html, "html.parser")

    table = soup.find("table")
    if table:
        print("\n=== Найдена таблица ===\n")
        print(table.prettify())
    else:
        print("\n=== Таблица НЕ найдена ===\n")

if __name__ == "__main__":
    test_fetch()
