# Backend image: the FastAPI app served by uvicorn.
FROM python:3.11-slim

# Show logs immediately and skip writing .pyc files.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install dependencies first so this layer stays cached until they change.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application source.
COPY . .

# The API listens on port 8000 inside the container.
EXPOSE 8000

# Start the server. Tables are created on startup (see the lifespan in
# src/main.py), so no separate migration step is needed.
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
