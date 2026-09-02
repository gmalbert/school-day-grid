FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY pyproject.toml ./
COPY school_day_grid ./school_day_grid
RUN pip install --no-cache-dir .
COPY templates ./templates
RUN mkdir -p /data
ENV SDG_DATABASE_PATH=/data/school_day_grid.sqlite3
EXPOSE 8088
CMD ["uvicorn", "school_day_grid.product_app:app", "--host", "0.0.0.0", "--port", "8088"]
