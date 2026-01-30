FROM python:3.10-slim
WORKDIR /app

# Установка правильной локали для UTF-8
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV PYTHONIOENCODING=utf-8

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p logs

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

CMD ["python3", "main.py"]

