# Используем базовый образ Python
FROM python:3.12

# Установка приложения и его зависимостей
WORKDIR /app
# копируем файл зависимостей приложения
COPY requirements.txt /app
# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt
# Копируем переменные окружения
COPY .env /app
# Копируем исходный код приложения внутрь контейнера
COPY /app /app
# Команда для запуска приложения
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]