# Dockerfile for Flask Chat App (fallback to ensure Python 3.11 runtime)
FROM python:3.11-slim

# Install build tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install 'setuptools>=68.0.0' wheel && pip install -r requirements.txt

COPY . /app

ENV PORT=5000
EXPOSE ${PORT}

CMD ["gunicorn", "--worker-class", "eventlet", "-w", "1", "wsgi:app", "--bind", "0.0.0.0:5000"]
