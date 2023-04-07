#!/bin/bash

OLD_CONT="$(docker ps -q --filter ancestor=complements-bot-py)"
docker build -t complements-bot-py . 1>/dev/null 2>&1

echo "$OLD_CONT"
