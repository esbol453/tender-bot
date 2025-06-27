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
                date_text = cols[3].text.strip()
                price_text = cols[4].text.strip().replace(" ", "").replace(" ", "")
                link = "https://goszakup.gov.kz" + cols[1].find("a")["href"]

                try:
                    price_value = float(price_text.replace("тг", "").replace(",", "."))
                except:
                    price_value = 0

                try:
                    tender_date = datetime.strptime(date_text, "%d.%m.%Y")
                except:
                    tender_date = None

                # Проверка даты
                if tender_date and tender_date < datetime.now() - timedelta(days=5):
                    continue

                # Загрузка страницы лота
                lot_resp = requests.get(link, timeout=10)
                lot_soup = BeautifulSoup(lot_resp.text, "html.parser")
                lot_text = lot_soup.get_text()

                # Проверка условий
                if (
                    "Место поставки: Мангистауская область" in lot_text and
                    "Статус: Опубликован (прием ценовых предложений)" in lot_text and
                    price_value <= 1_000_000 and
                    (
                        "Товар" in lot_text or
                        "Товары" in lot_text or
                        "товар" in lot_text
                    )
                ):
                    tenders.append({
                        "title": title,
                        "price": price_text,
                        "date": date_text,
                        "url": link
                    })

    except Exception as e:
        tenders.append({"title": f"Ошибка: {e}", "price": "", "date": "", "url": ""})

    return tenders
