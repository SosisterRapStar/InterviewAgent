FROM python:3.10-slim
WORKDIR /app
RUN apt-get update && apt-get clean && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p logs
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
CMD ["python3", "main.py"]

