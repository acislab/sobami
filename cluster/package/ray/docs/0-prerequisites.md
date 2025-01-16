# Environment Variables Configuration

## Authentication
- `HF_TOKEN`: Hugging Face authentication token
  > Get from: https://huggingface.co/settings/tokens

## Ray Network Configuration
- `RAY_HEAD_NODE_IP`: IP address of the Ray head node
  > Find using: `hostname -I | awk '{print $1}'`
- `RAY_HEAD_NODE_PORT`: Port for Ray head node (default: 3002)
- `RAY_DASHBOARD_HOST`: Ray dashboard host address (default: 0.0.0.0)
- `RAY_DASHBOARD_PORT`: Ray dashboard port (default: 5678)

## Hardware Configuration
- `RAY_HEAD_ETHERNET_DEVICE`: Ethernet network interface for Ray head node
  > Find using: `ifconfig'`
- `RAY_HEAD_GPU_COUNT`: Number of GPUs allocated to head node
  > Check number of gpus on current node using: `nvidia-smi --list-gpus | wc -l`
- `RAY_WORKER_1_ETHERNET_DEVICE`: Ethernet network interface for Ray worker
- `RAY_WORKER_1_GPU_COUNT`: Number of GPUs allocated to worker
- `SHM_SIZE`: Shared memory size (default: 10.24gb)
  > Check available: `df -h /dev/shm`

## Docker Configuration
- `SWARM_MANAGER_DOCKER_IMAGE`: Docker image for manager example: vllm/vllm-openai:v0.6.6
- `SWARM_WORKER_DOCKER_IMAGE`: Docker image for workers

## Path Configuration
- `SWARM_MANAGER_PATH_TO_HF_HOME`: Hugging Face home directory path for manager
  > Default: `~/.cache/huggingface`
- `SWARM_MANAGER_PATH_TO_TMP_RAY`: Temporary Ray directory path for manager
  > Default: `/tmp/ray`
- `SWARM_WORKER_PATH_TO_HF_HOME`: Hugging Face home directory path for worker
- `SWARM_WORKER_PATH_TO_TMP_RAY`: Temporary Ray directory path for worker