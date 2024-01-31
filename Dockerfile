# syntax=docker/dockerfile:1

FROM python:3.12-alpine3.19
WORKDIR /complements-bot-py
ENV PYTHONPATH /complements-bot-py
COPY src ./src
COPY main.py .
RUN rm -rf ./src/test_complements_bot
RUN pip install pipenv
RUN apk update
RUN apk add gcc
RUN apk add musl-dev
RUN apk add python3-dev
RUN apk add libffi-dev
RUN apk add openssl-dev
RUN apk add cargo
RUN apk add build-base
RUN cd ./src; pipenv install --system --deploy; cd ..
RUN rm -rf /var/cache/apk/*
RUN pip install cython

RUN find /usr -name Python.h

RUN python3-config --includes
RUN python3-config --includes | grep python3.12

RUN python -m cython -3 --embed -o main.c main.py
RUN gcc -Os -I $(python3-config --includes | grep python3.12) -o main main.c -lpython3.12 -lpthread -lutil $(python3-config --libs)
# EXPOSE 50994/tcp
# EXPOSE 50995/tcp
CMD ["./main"]
