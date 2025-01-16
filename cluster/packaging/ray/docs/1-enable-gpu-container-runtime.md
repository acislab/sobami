## GPU Setup for Docker Swarm

### Prerequisites Check
```bash
nvidia-container-toolkit --version
```

### GPU Configuration

1. **Identify GPU UUIDs**
```bash
nvidia-smi -L
# Output example: GPU 0: NVIDIA A100-PCIE-40GB (UUID: GPU-UUID)
```

2. **Configure Docker Runtime**
Edit `/etc/docker/daemon.json`:
```json
{
    "default": "nvidia",
    "node-generic-resources": [
        "NVIDIA-GPU=GPU-UUID"
    ]
}
```

3. **Enable Swarm Support**
Edit `/etc/nvidia-container-runtime/config.toml`:
```toml
swarm-resource = "DOCKER_RESOURCE_NVIDIA-GPU"
```

### Apply Changes

```bash
sudo systemctl restart docker.service
```

Note: This configuration enables NVIDIA GPU support in Docker Swarm mode, which is not supported by default Docker.