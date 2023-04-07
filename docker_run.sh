#!/bin/bash

if [ -z "$1" ]
  then
  docker stop "$(docker ps -q --filter ancestor=complements-bot-py)" || true
else
  docker stop "$1" || true
fi

docker run -dP complements-bot-py
