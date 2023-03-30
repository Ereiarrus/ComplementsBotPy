#!/bin/bash

docker kill complements-bot-py || true
docker run -dP complements-bot-py
