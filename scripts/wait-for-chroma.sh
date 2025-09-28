#!/bin/bash
# scripts/wait-for-chroma.sh

set -e

host="$CHROMA_HOST"
port="$CHROMA_PORT"

echo "Waiting for ChromaDB at $host:$port..."

for i in {1..30}; do
    if curl -f "http://$host:$port/api/v2/heartbeat" >/dev/null 2>&1; then
        echo "ChromaDB is up - executing command"
        exec "$@"
    fi
    echo "ChromaDB not ready yet, waiting... (attempt $i/30)"
    sleep 2
done

echo "ChromaDB failed to start within 60 seconds"
exit 1
