# syntax=docker/dockerfile:1

FROM python:3.9-alpine
WORKDIR /
COPY . .
RUN pip install -r requirements.txt
# CMD ["python", "main.py"]
RUN pip install cython
RUN python -m cython main.py --embed
RUN gcc -o main main.c
CMD ["./main"]
EXPOSE 4000
