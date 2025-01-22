# Environment Variables Configuration

## Authentication
- `HF_TOKEN`: Hugging Face authentication token
  > Get from: https://huggingface.co/settings/tokens

## Ray Network Configuration
- `RAY_HEAD_NODE_IP`: IP address of the Ray head node
  > Find using: `hostname -I | awk '{print $1}'`
- `RAY_HEAD_NODE_PORT`: Port for Ray head node example: 3002
- `RAY_DASHBOARD_HOST`: Ray dashboard host address example: 0.0.0.0
- `RAY_DASHBOARD_PORT`: Ray dashboard port example: 5678

## Hardware Configuration
- `RAY_HEAD_ETHERNET_DEVICE`: Ethernet network interface for Ray head node
  > Find using: `ifconfig'`
- `RAY_HEAD_GPU_COUNT`: Number of GPUs allocated to head node
  > Check number of gpus on current node using: `nvidia-smi --list-gpus | wc -l`
- `RAY_WORKER_1_ETHERNET_DEVICE`: Ethernet network interface for Ray worker
- `RAY_WORKER_1_GPU_COUNT`: Number of GPUs allocated to worker

## Container Configuration
- `SHM_SIZE`: Shared memory size example: 10.24gb
- `MEMORY_SIZE`: Assigned memory size to the container example: 16gb
  > Check available: `df -h /dev/shm`
- `CPUS`: Assigned number of CPUs to the container example: 12
  > Check number of CPUs on current node: `lscpu | grep 'CPU(s):'`

## vLLM Server Configuration
- `MODEL`: Intended LLM to run on this setup example: `meta-llama/Llama-3.2-1B-Instruct`
  > List of supported models: https://docs.vllm.ai/en/latest/models/supported_models.html

## Docker Configuration
- `SWARM_MANAGER_DOCKER_IMAGE`: Docker image for manager example: vllm/vllm-openai:v0.6.6
- `SWARM_WORKER_DOCKER_IMAGE`: Docker image for workers
- `SWARM_MANAGER_PATH_TO_HF_HOME`: Hugging Face home directory path for manager
  > Default HF directory on Linux: `~/.cache/huggingface`
- `SWARM_MANAGER_PATH_TO_TMP_RAY`: Temporary Ray directory path for manager
  > Default Ray directory on Linux: `~/tmp/ray`
- `SWARM_WORKER_PATH_TO_HF_HOME`: Hugging Face home directory path for worker
- `SWARM_WORKER_PATH_TO_TMP_RAY`: Temporary Ray directory path for worker