#!/bin/bash

# Note: Only run if placement_groups are pending even if no deployments
# This script starts a Docker container using the specified Ray image,
# connects to the Ray cluster (using host network), and executes Python code
# within the container to remove all Ray Placement Groups.

# --- Configuration ---
readonly DOCKER_IMAGE="rayproject/ray:2.44.1-py312-gpu"
readonly NETWORK_MODE="host"
export RAY_ADDRESS="http://10.13.44.223:3002"

# --- Main Script ---
echo "Starting Docker container to clean up Ray Placement Groups..."

docker_env_opts=""
if [[ -n "${RAY_ADDRESS}" ]]; then
    docker_env_opts="-e RAY_ADDRESS=${RAY_ADDRESS}"
fi

# Documentation: https://github.com/ray-project/ray/blob/ray-2.7.0/python/ray/util/placement_group.py#L291
# https://github.com/ray-project/ray/issues/22774#issuecomment-2111576499
if docker run --rm --network "${NETWORK_MODE}" ${docker_env_opts} "${DOCKER_IMAGE}" python - <<EOF
import ray
import sys
from ray._raylet import PlacementGroupID
from ray._private.utils import hex_to_binary
from ray.util.placement_group import (
    PlacementGroup,
    placement_group_table,
    remove_placement_group,
)

exit_code = 0
try:
    ray_address = os.environ.get("RAY_ADDRESS", "auto")
    ray.init(address=ray_address, ignore_reinit_error=True)

    for placement_group_info in placement_group_table().values():
        pg = PlacementGroup(
            PlacementGroupID(hex_to_binary(placement_group_info["placement_group_id"]))
        )
        remove_placement_group(pg)

except Exception:
    exit_code = 1
finally:
    if ray.is_initialized():
        ray.shutdown()

sys.exit(exit_code)
EOF
then
        echo "Placement group cleanup script executed successfully."
        exit 0
else
        exit_code=$?
        echo "Error: Placement group cleanup script failed (Exit Code: ${exit_code})." >&2
        exit ${exit_code}
fi
