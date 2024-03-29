#!/bin/bash


old_container_id="$(./docker_build.sh)"
build_status="$?"
if [ "$build_status" != 0 ]; then
  >&2 echo "error on docker build"
  exit "$build_status"
fi

if [ -z "$old_container_id" ]; then
  previous_container="$(docker ps -q --filter ancestor=complements-bot-py)"
  if [ -n "$previous_container" ]; then
    docker stop previous_container
  fi
else
  restarter="$(pgrep restart_24.sh)"
  kill "$restarter"
  docker stop "$old_container_id" > /dev/null 2>&1
fi

container_id="$(docker run \
  -d \
  --restart=unless-stopped \
  --log-opt max-size=50m \
  --log-opt max-file=3 \
  complements-bot-py \
)"
run_status="$?"
if [ "$run_status" != 0 ]; then
  >&2 echo "error on docker run"
  exit "$run_status"
fi

nohup ./restart_24.sh "$container_id" 1>&2  2>./restart.log &
