FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY monitor ./monitor
COPY main.py config.yaml ./

RUN mkdir -p /app/logs && useradd --create-home --uid 10001 monitor \
    && chown -R monitor:monitor /app
USER monitor

CMD ["python", "main.py"]
