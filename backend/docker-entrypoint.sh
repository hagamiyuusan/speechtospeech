#!/bin/bash
set -e

# If a mounted config.yaml exists, use it; otherwise, use the template
if [ ! -f "/app/config.yaml" ]; then
    echo "No config.yaml found, using template..."
    cp /app/config.yaml.template /app/config.yaml
fi

# Execute the main command
exec "$@"