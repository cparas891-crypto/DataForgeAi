FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/requirements.txt

RUN python -m pip install --no-cache-dir --upgrade -r /app/requirements.txt

COPY app.py /app/app.py
COPY config.py /app/config.py
COPY database.py /app/database.py

COPY services /app/services
COPY routes /app/routes
COPY templates /app/templates

RUN mkdir -p /app/uploads /app/cleaned /app/reports

EXPOSE 8010

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8010"]