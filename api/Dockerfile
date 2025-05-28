FROM python:3.11-slim

WORKDIR /app

# Copy requirements.txt from root because context is root which is set in docker-compose.yml
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy API source code from api directory into container
COPY api/ .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
