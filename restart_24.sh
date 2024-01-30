#!/bin/bash

# Docker container ID or name
container_id="$1"
if [ -z "$container_id" ]; then
  container_id=$(docker ps -q --filter name=complements-bot-py)
fi

# Function to restart the Docker container
restart_container() {
  docker restart "$container_id"
}

# Function to start the Docker container if restart fails
start_container() {
  docker start "$container_id"
}

# Run indefinitely
while true; do
  # Wait for 24 hours before next attempt (86400 seconds)
  sleep 86400
  # Try to restart the container
  if ! restart_container; then
    echo "Restart failed, trying to start the container..."
    start_container
  fi
done
