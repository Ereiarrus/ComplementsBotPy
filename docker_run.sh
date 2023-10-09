#!/bin/bash


STATUS_FILE=$1
if [ -z "$STATUS_FILE"  ]; then
  STATUS_FILE=./status.txt
fi


old_container_id="$(./docker_build.sh)"
build_status="$?"


if [ "$build_status" != 0 ]; then
  exit "$build_status"
fi

if [ -z "$old_container_id" ]; then
  previous_container="$(docker ps -q --filter ancestor=complements-bot-py)"
  if [ -n "$previous_container" ]; then
    docker stop previous_container
  fi
else
  docker stop "$old_container_id" > /dev/null 2>&1
fi

docker run \
-d \
-p 50995:50995 \
-p 50994:50994 \
--restart=unless-stopped \
--log-opt max-size=50m \
--log-opt max-file=3 \
--log-driver local \
complements-bot-py \

