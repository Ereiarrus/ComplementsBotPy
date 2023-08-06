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

container_id="$(\
  docker run \
  -dP \
  --restart=unless-stopped \
  -v "$STATUS_FILE":/status.txt \
  -v ./app.log:/app.log \
  -v ./app.log.1:/app.log.1 \
  -v ./app.log.2:/app.log.2 \
  -v ./app.log.3:/app.log.3 \
  --log-opt max-size=50m \
  --log-opt max-file=3 \
  complements-bot-py \
)"

container_id_file=./container_id.txt

(echo "$container_id") > "$container_id_file"

date +%s > "$STATUS_FILE"

threshold=$((60 * 60))
while [ "$(cat $container_id_file)" == "$container_id" ]; do
    if [ $(($(date +%s) - $(cat "$STATUS_FILE"))) -gt $threshold ]; then
        (echo "$container_id at $(date +%s) -  Detected situation where docker container was working, but bot was not!") >> ./while_loop_log.txt
        date +%s > "$STATUS_FILE"
        docker restart "$container_id"
    fi
    sleep $((14 * 60))
done >>./while_loop_log.txt 2>>./while_loop_log.txt &
