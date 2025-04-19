## Overview

<div style="text-align: center;">
    <img src="sobami.png" alt="sobami-cluster" style="width: auto; height: 500px;">
    <p>This image shows the Sobami cluster setup.</p>
</div>
    
## Docker Images

| Image Name                         | Description                                                                 | Dockerfile         | Links                                                    |
| ----------------------------------- | --------------------------------------------------------------------------- | ------------------ | -------------------------------------------------------- |
| nitingoyal0996/ray_2.44.1:extended | Based on `rayproject/ray:2.44.1-py312-gpu` with extra `ray[llm]` dependencies | Dockerfile.node    | https://hub.docker.com/r/nitingoyal0996/ray_2.44.1       |
| serve                              | Based on `rayproject/ray:2.44.1-py312-gpu` to deploy the app on the Ray cluster | Dockerfile.serve   | https://hub.docker.com/r/rayproject/ray:2.44.1-py312-gpu |
| rayproject/ray:2.44.1-py312-gpu    | Main Ray image for distributed computing                                    | N/A                | https://hub.docker.com/r/rayproject/ray:2.44.1-py312-gpu |

## How does it work?

Ray runs as Docker services using the host machine's network. When a Ray[LLM] app starts in a container, it connects to the running Ray cluster.

Prometheus uses a service discovery JSON file to find and scrape metrics from the latest Ray session.

## Cluster Services

| Service Name   | Address       | Description                              |
| -------------- | ------------- | ---------------------------------------- |
| Ray Cluster    | SOBAMI1:3002  | Main Ray service                         |
| Ray Dashboard  | SOBAMI1:5678  | Web UI to monitor the Ray cluster        |
| Prometheus     | SOBAMI1:9090  | Collects and stores metrics              |
| Grafana        | SOBAMI1:3000  | Shows dashboards for cluster metrics     |

## Scripts

1. `deploy_cluster.sh`: Updates Docker service configs and deploys them with Docker Swarm.
2. `build_deploy_serve.sh`: This script builds the Docker image, deploys the Ray cluster, and serves the LLM application.
3. `stop_serve.sh`: Connects to the running ray cluster and shutdown LLM application. 

## Docker Stack Management Guide

Followed the tutorial [here](https://docs.docker.com/engine/swarm/swarm-tutorial/create-swarm/) to create a swarm of nodes


### Basic Commands

**Manually Generate `docker compose` Configurations**

<!-- generates the config > replaces the cpu number (12) to string ('12') > removes the first line > saves it to a file -->

```bash
docker compose --env-file .env config | sed -E "s/cpus: ([0-9\\.]+)/cpus: '\\1'/" | tail -n +2 > docker-compose-configured.yml
```

**Deploy Stack**
```bash
docker stack deploy -c docker-compose-configured.yml ray
```

**Monitor Stack**
```bash
# List all stacks
docker stack ls
# NAME      SERVICES
# ray       2

# List all services
docker service ls

# Check service status
docker service ps ray_<service-name>

# View running containers
docker ps
```
Note: Container names follow the pattern: `deployment_name.replica-number.uuid`

### Troubleshooting
If services fail:
```bash
# View complete error messages
docker service ps deployment_name --no-trunc

# Check detailed service logs
docker service logs deployment_name --details
```
