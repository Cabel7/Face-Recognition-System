FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && apt-get clean

WORKDIR /app
COPY . .

RUN pip install --upgrade pip

# install base deps (including Pillow)
RUN pip install --no-cache-dir -r requirements.txt

# install dlib (prebuilt)
RUN pip install --no-cache-dir dlib-bin==19.24.2

# install face recognition (no deps)
RUN pip install --no-cache-dir --no-deps face-recognition==1.3.0

RUN pip install --no-cache-dir git+https://github.com/ageitgey/face_recognition_models

EXPOSE 10000

CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000"]
