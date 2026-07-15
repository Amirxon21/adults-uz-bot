FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Render/Railway kabi platformalar PORT muhit o'zgaruvchisini o'zi beradi
ENV PORT=8000
EXPOSE 8000

CMD uvicorn api:app --host 0.0.0.0 --port ${PORT}
