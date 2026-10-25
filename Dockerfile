
FROM node:22-slim AS frontend-build

WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend /app/backend
COPY --from=frontend-build /frontend/dist /app/frontend/dist
COPY run.py /app/run.py

ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["python", "run.py"]
