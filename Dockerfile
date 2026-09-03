FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY pyproject.toml ./
COPY *.py ./
RUN pip install --no-cache-dir .
COPY templates ./templates
COPY static ./static
RUN mkdir -p /data
ENV SDG_DATABASE_PATH=/data/school_day_grid.sqlite3
EXPOSE 8088
CMD ["uvicorn", "product_app:app", "--host", "0.0.0.0", "--port", "8088"]
