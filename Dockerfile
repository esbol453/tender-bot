# Используем стабильный Python 3.11
FROM python:3.11-slim

# Создаем рабочую папку
WORKDIR /app

# Копируем файлы проекта в контейнер
COPY . /app

# Устанавливаем зависимости
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Запускаем бота
CMD ["python", "main.py"]
