FROM python:3.11-slim

WORKDIR /app

COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY ./shared /app/shared
COPY ./services/wms/app /app/app
COPY ./services/wms/alembic /app/alembic
COPY ./services/wms/alembic.ini /app/alembic.ini

ENV PYTHONPATH=/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
