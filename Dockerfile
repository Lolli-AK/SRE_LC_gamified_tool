FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
COPY app/data/problems.json /app/problems.json
ENV PROBLEMS_PATH=/app/problems.json

RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]