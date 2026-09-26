# Production image: inference only (MODEL_CONTRACT.md §4). numpy + stdlib.
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DATA_DIR=/data PORT=8080
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY aitrader ./aitrader
COPY models ./models
COPY research ./research
RUN useradd --create-home --uid 10001 app && mkdir -p /data && chown -R app /data
USER app
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s CMD python -c "import urllib.request,os;urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"PORT\",\"8080\")}/healthz',timeout=4)"
CMD ["python", "-m", "aitrader"]
