# syntax=docker/dockerfile:1

FROM python:3.10-alpine
WORKDIR /
COPY src .
RUN apk add python3-dev
RUN apk add build-base
RUN pip install -r requirements.txt
RUN pip install cython
RUN python -m cython --embed -o main.c main.py
RUN gcc -Os -I /usr/include/python3.10 -o main main.c -lpython3.10 -lpthread -lm -lutil -ldl
CMD ["./main"]
