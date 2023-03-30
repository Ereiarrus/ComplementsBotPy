#!/bin/bash

docker stop "$(docker ps -q --filter ancestor=complements-bot-py)" || true
docker run -dP complements-bot-py
