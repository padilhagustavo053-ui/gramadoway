FROM python:3.11-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Pasta de dados persistente (monte volume em /data em produção)
ENV GRAMADOWAY_DATA_DIR=/data
RUN mkdir -p /data

EXPOSE 8000 8501
