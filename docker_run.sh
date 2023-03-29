#!/bin/bash

docker kill complements-bot-py
docker run -dP complements-bot-py
