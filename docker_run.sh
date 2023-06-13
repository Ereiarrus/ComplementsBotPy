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
  docker stop "$(docker ps -q --filter ancestor=complements-bot-py)" || true
else
  docker stop "$old_container_id" > /dev/null 2>&1
fi

container_id="$(docker run -dP --restart=unless-stopped -v ./status.txt:/status.txt --log-opt max-size=50m --log-opt max-file=3 complements-bot-py)"

container_id_file=./container_id.txt

(echo "$container_id") > "$container_id_file"

date +%s > "$STATUS_FILE"

threshold=$((60))
while [ "$(cat $container_id_file)" == "$container_id" ]; do
    if [ $(($(date +%s) - $(cat "$STATUS_FILE"))) -gt $threshold ]; then
        (echo "$container_id at $(date +%s) -  Detected situation where docker container was working, but bot was not!") >> ./while_loop_log.txt
        date +%s > "$STATUS_FILE"
        docker restart "$container_id"
    fi
    sleep $((14 * 60))
done >/dev/null 2>&1 &
