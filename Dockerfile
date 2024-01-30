# syntax=docker/dockerfile:1

FROM python:3.12-alpine
WORKDIR /complements-bot-py
ENV PYTHONPATH /complements-bot-py
COPY src ./src
COPY main.py .
RUN rm -rf ./src/test_complements_bot
RUN pip install pipenv
RUN apk add --no-cache \
    gcc \
    musl-dev \
    python3-dev \
    libffi-dev \
    openssl-dev \
    cargo \
    build-base
RUN cd ./src; pipenv install --system --deploy; cd ..
RUN apk add python3-dev
RUN apk add build-base
RUN pip install cython
RUN python -m cython -3 --embed -o main.c main.py
RUN gcc -Os -I /usr/include/python3.12 -o main main.c -lpython3.12 -lpthread -lm -lutil -ldl
# EXPOSE 50994/tcp
# EXPOSE 50995/tcp
CMD ["./main"]
