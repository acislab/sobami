#!/bin/bash

set -e
set -o pipefail

# --- Configuration ---
readonly STACK_NAME="ray"
readonly ENV_FILE=".env"

TEMP_COMPOSE_FILE=$(mktemp)

# --- Cleanup Function ---
cleanup() {
    rm -f "$TEMP_COMPOSE_FILE"
}
trap cleanup EXIT HUP INT QUIT TERM

# --- Main Script ---
echo "Generating Docker Compose configuration for stack '$STACK_NAME'..."
docker compose --env-file "$ENV_FILE" config | \
    sed -E "s/cpus: ([0-9\\.]+)/cpus: '\\1'/" | \
    tail -n +2 > "$TEMP_COMPOSE_FILE" # Note: HACK to produce docker stack config file
fi

if [ ! -s "$TEMP_COMPOSE_FILE" ]; then
        echo "Error: Generated configuration file is empty. Check 'docker compose config' output." >&2
        exit 1
fi

echo "Deploying stack '$STACK_NAME'..."
docker stack deploy --with-registry-auth -c "$TEMP_COMPOSE_FILE" "$STACK_NAME"

echo "Stack '$STACK_NAME' deployment command executed successfully."

exit 0
