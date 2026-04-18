FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ensure model directory exists
RUN mkdir -p models

EXPOSE 5000

CMD ["python", "main.py"]
