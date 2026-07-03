FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml requirements.txt ./

RUN pip install uv && uv pip install --system -r requirements.txt

COPY . .

ENV PYTHONPATH=/app/src

EXPOSE 8000
