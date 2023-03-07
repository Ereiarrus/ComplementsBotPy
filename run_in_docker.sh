#!/bin/bash

if [ $# -eq 0 ]; then
  echo "Error: No token provided"
  exit 1
fi

set -a
source .env

received_github_token="$1"

if "$TMI_TOKEN" != "$received_github_token"; then
  echo "Wrong sender; exiting"
  exit 2
fi

(exec "git pull")
(exec "./docker_build.sh")
if ! docker kill complements-bot-py >/dev/null 2>&1; then
  echo "Did not find any pre-existing complements-bot-py process that could be terminated; continuing as normal.";
fi
(exec "./docker_run.sh")

set +a
