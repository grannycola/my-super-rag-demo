FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir "numpy>=1.26.0,<2.4.0"

COPY . .

EXPOSE 8081

CMD ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8081"]
