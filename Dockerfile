# Production image: inference only (MODEL_CONTRACT.md §4). numpy + stdlib.
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DATA_DIR=/data PORT=8080
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY aitrader ./aitrader
COPY models ./models
COPY research ./research
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN useradd --create-home --uid 10001 app && mkdir -p /data && chown -R app /data
# Starts as root only to take ownership of a mounted volume (Railway mounts
# volumes as root), then drops to uid 10001 before the service starts.
ENTRYPOINT ["docker-entrypoint.sh"]
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s CMD python -c "import urllib.request,os;urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"PORT\",\"8080\")}/healthz',timeout=4)"
CMD ["python", "-m", "aitrader"]
