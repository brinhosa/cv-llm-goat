# Build context = cv_injection_lab (parent), so payloads.py is available.
FROM python:3.12-slim

WORKDIR /app
COPY webapp/requirements.txt /app/webapp/requirements.txt
RUN pip install --no-cache-dir -r /app/webapp/requirements.txt

COPY payloads.py /app/payloads.py
COPY webapp /app/webapp

# Run unprivileged: the app parses untrusted PDFs and never needs root.
RUN useradd --uid 10001 --create-home --shell /usr/sbin/nologin app
USER app

WORKDIR /app/webapp
EXPOSE 8090
CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8090"]
