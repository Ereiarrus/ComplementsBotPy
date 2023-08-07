# syntax=docker/dockerfile:1

FROM python:3.10-alpine
WORKDIR /complements-bot-py
ENV PYTHONPATH /complements-bot-py
COPY src ./src
COPY main.py .
RUN rm -rf ./src/test_complements_bot
RUN pip install -r ./src/requirements.txt
RUN apk add python3-dev
RUN apk add build-base
RUN pip install cython
RUN python -m cython -3 --embed -o main.c main.py
RUN gcc -Os -I /usr/include/python3.10 -o main main.c -lpython3.10 -lpthread -lm -lutil -ldl
EXPOSE 50994/tcp
EXPOSE 50995/tcp
CMD ["./main"]
