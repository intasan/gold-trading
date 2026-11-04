FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt requirements-postgres.txt ./
RUN pip install --no-cache-dir -r requirements-postgres.txt && useradd --uid 10001 --create-home pipeline
COPY --chown=pipeline:pipeline . .
RUN mkdir -p /app/data/raw && chown -R pipeline:pipeline /app/data
USER pipeline
CMD ["python", "-m", "goldtrading", "refresh"]
