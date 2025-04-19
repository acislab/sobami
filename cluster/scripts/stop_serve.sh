#!/bin/bash
# This script attempts to gracefully shut down a Ray Serve instance.
# It uses a Docker container with the specified Ray image to execute the
# `serve shutdown` command against the configured SERVE_ADDRESS.

set -euo pipefail

# --- Configuration ---
readonly SERVE_ADDRESS="${SERVE_ADDRESS:-http://10.13.44.223:5678}"
readonly DOCKER_IMAGE="rayproject/ray:2.44.1-py312-gpu"
readonly NETWORK_MODE="host"

# --- Main Script ---
echo "Attempting to send shutdown command to serve service at ${SERVE_ADDRESS}..."

if docker run --rm --network "${NETWORK_MODE}" "${DOCKER_IMAGE}" \
		serve shutdown --address="${SERVE_ADDRESS}" -y; then
	echo "Shutdown command sent successfully to ${SERVE_ADDRESS}."
	exit 0
else
	exit_code=$?
	echo "Error: Failed to send shutdown command (Exit Code: ${exit_code})." >&2
	if curl --fail --silent --output /dev/null "${SERVE_ADDRESS}"; then
		echo "Service at ${SERVE_ADDRESS} might still be running." >&2
	else
		echo "Service at ${SERVE_ADDRESS} appears to be down already." >&2
	fi
	exit ${exit_code}
fi