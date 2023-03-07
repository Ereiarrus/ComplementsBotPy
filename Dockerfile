# syntax=docker/dockerfile:1

FROM python:3.10-alpine
WORKDIR /src
COPY src/complements_bot .
COPY src/.env .
COPY src/.firebase_config.json .
COPY src/env_reader.py .
COPY src/main.py .
COPY src/pyproject.toml .
COPY src/requirements.txt .
RUN pip install -r requirements.txt
RUN apk add python3-dev
RUN apk add build-base
RUN pip install cython
RUN python -m cython -3 --embed -o main.c main.py
RUN gcc -Os -I /usr/include/python3.10 -o main main.c -lpython3.10 -lpthread -lm -lutil -ldl
CMD ["./main"]
