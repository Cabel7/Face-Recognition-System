FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && apt-get clean

WORKDIR /app
COPY . .

RUN pip install --upgrade pip

# Install base deps
RUN pip install --no-cache-dir flask gunicorn numpy opencv-python-headless

# 🔥 Install prebuilt dlib ONLY
RUN pip install --no-cache-dir dlib-bin==19.24.2

# 🔥 Install face-recognition WITHOUT dependencies
RUN pip install --no-cache-dir --no-deps face-recognition==1.3.0

EXPOSE 10000

CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000"]
