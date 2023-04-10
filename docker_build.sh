#!/bin/bash

OLD_CONT="$(docker ps -q --filter ancestor=complements-bot-py)"
docker build -t complements-bot-py . 1>"./stdout.log" 2>"./stderr.log"

docker_build_out="$?"

if [ "$docker_build_out" != 0 ]
  then
  >&2 echo "Error $docker_build_out - Docker container could not be built:"
  cat "./stderr.log" 1>&2
  exit "$docker_build_out"
fi

echo "$OLD_CONT"
