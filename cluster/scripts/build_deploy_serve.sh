
#!/bin/bash
set -euo pipefail

# --- Configuration ---
APP_NAME="serve_app"
RAY_ADDRESS="${RAY_ADDRESS:-10.13.44.223:3002}"
CONTAINER_NAME="${APP_NAME}_container"

# --- Script Variables ---
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
PROJECT_ROOT=$(realpath "$SCRIPT_DIR/..")
SERVE_DIR="$PROJECT_ROOT/serve/src"
DOCKER_DIR="$PROJECT_ROOT/docker"
DOCKERFILE="$DOCKER_DIR/Dockerfile.serve"
IMAGE_TAG="serve:latest"

# --- Functions ---
error_exit() {
    echo "$(date +"%Y-%m-%d %H:%M:%S") - ERROR - $1" >&2
    # Clean up build context if it exists
    [[ -n "${BUILD_CONTEXT-}" && -d "$BUILD_CONTEXT" ]] && rm -rf "$BUILD_CONTEXT"
    exit 1
}

cleanup() {
    echo "Cleaning up temporary build context: $BUILD_CONTEXT"
    rm -rf "$BUILD_CONTEXT"
    echo "Temporary build files cleaned up."
}

# --- Main Execution ---
echo "Starting build and deploy process..."
BUILD_CONTEXT="docker_build_context_$(date +"%d%m%y_%H%M")"
mkdir -p "$BUILD_CONTEXT"
echo "Created temporary build context: $BUILD_CONTEXT"

# Set trap for cleanup on exit or error
trap cleanup EXIT

[[ ! -f "$SERVE_DIR/serve.py" ]] && error_exit "Source file not found: $SERVE_DIR/serve.py"
[[ ! -f "$SERVE_DIR/start.sh" ]] && error_exit "Source file not found: $SERVE_DIR/start.sh"
[[ ! -f "$DOCKERFILE" ]] && error_exit "Dockerfile not found: $DOCKERFILE"
echo "Copying files to build context..."
cp "$SERVE_DIR/serve.py" "$BUILD_CONTEXT/" || error_exit "Failed to copy serve.py"
cp "$SERVE_DIR/start.sh" "$BUILD_CONTEXT/" || error_exit "Failed to copy start.sh"
cp "$DOCKERFILE" "$BUILD_CONTEXT/Dockerfile.serve" || error_exit "Failed to copy Dockerfile.serve"
echo "Files copied successfully."

echo "Building Docker image: $IMAGE_TAG"
if docker build -t "$IMAGE_TAG" -f "$BUILD_CONTEXT/Dockerfile.serve" "$BUILD_CONTEXT"; then
    echo "Build complete: $IMAGE_TAG"
else
    error_exit "Docker build failed."
fi

if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "Stopping existing container: $CONTAINER_NAME"
    docker stop "$CONTAINER_NAME" || echo "Failed to stop container (may already be stopped)."
    echo "Removing existing container: $CONTAINER_NAME"
    docker rm "$CONTAINER_NAME" || error_exit "Failed to remove existing container: $CONTAINER_NAME"
fi

echo "Deploying Docker container '$CONTAINER_NAME' from image: $IMAGE_TAG"
echo "Using RAY_ADDRESS: $RAY_ADDRESS"
echo "Mapping host path '/home/nitingoyal/storage/tmp/ray' to container path '/tmp/ray'"

docker run \
    --name "$CONTAINER_NAME" \
    --network host \
    -v /home/nitingoyal/storage/tmp/ray:/tmp/ray \
    -e RAY_ADDRESS="$RAY_ADDRESS" \
    "$IMAGE_TAG";

echo "Container '$CONTAINER_NAME' started successfully."
echo "To view logs: docker logs $CONTAINER_NAME"


echo "Deployment process finished."

exit 0
