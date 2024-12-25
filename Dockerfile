FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY Pipfile* .

RUN pip install pipenv && pipenv install --system --deploy

COPY . .

CMD ["python", "main.py"]
