FROM python:3.13.18-slim-trixie

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /usr/local/app
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip==26.3 && \
    pip install --no-cache-dir -r requirements.txt && \
    useradd --create-home --uid 10001 --shell /usr/sbin/nologin appuser
COPY --chown=appuser:appuser . .
USER appuser
EXPOSE 8080
CMD ["gunicorn", "app:app", "-b", "0.0.0.0:8080", "--log-file", "-", "--access-logfile", "-", "--workers", "4", "--keep-alive", "0"]
