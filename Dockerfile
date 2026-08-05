FROM python:3.10-slim

# Test Run 4
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && apt-get clean

WORKDIR /app

COPY . .

RUN pip install --upgrade pip

RUN pip install --no-cache-dir -r requirements.txt

RUN pip install --no-cache-dir dlib-bin==19.24.2

RUN pip install --no-cache-dir --no-deps face-recognition==1.3.0

# unable to install dblib normally
RUN pip install --no-cache-dir face-recognition-models

EXPOSE 10000

CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000"]
