FROM python:3.10-slim

# Install only minimal system libs (avoid heavy build tools)
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && apt-get clean

WORKDIR /app

COPY . .

RUN pip install --upgrade pip

# 🔥 Avoid dlib compilation
RUN pip install --prefer-binary --no-cache-dir -r requirements.txt

EXPOSE 10000

CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000"]