FROM python:3.11-slim

WORKDIR /app

COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY ./shared /app/shared
COPY ./services/finance/app /app/app
COPY ./services/finance/alembic /app/alembic
COPY ./services/finance/alembic.ini /app/alembic.ini

ENV PYTHONPATH=/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
