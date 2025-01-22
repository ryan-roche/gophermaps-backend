#!/bin/bash

max_attempts=30
attempt=1

while [ $attempt -le $max_attempts ]; do
    if systemctl is-active --quiet gophermaps.service; then
        echo "Service started successfully"
        exit 0
    fi
    echo "Attempt $attempt: Service not ready, waiting..."
    sleep 10
    ((attempt++))
done

echo "Service failed to start after $max_attempts attempts"
exit 1