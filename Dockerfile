# syntax=docker/dockerfile:1

FROM python:3.9-alpine
WORKDIR /
COPY . .
RUN apk add build-base
RUN apk add python3-dev
RUN pip install -r requirements.txt
# CMD ["python", "main.py"]
RUN pip install cython
RUN python -m cython --embed -o main.c main.py
RUN gcc -Os -I /usr/include/python3.9m -o main main.c -lpython3.9m -lpthread -lm -lutil -ldl
CMD ["./main"]
EXPOSE 4000
