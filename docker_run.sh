#!/bin/bash

old_container_id="$(./docker_build.sh)"
build_status="$?"

if [ "$build_status" != 0 ]
  then
  exit "$build_status"
fi

if [ -z "$old_container_id" ]
  then
  docker stop "$(docker ps -q --filter ancestor=complements-bot-py)" || true
else
  docker stop "$old_container_id"
fi

docker run -dP complements-bot-py
