## Docker Stack Management Guide

### Setting Up
Create a `docker-compose.yml` file with service specifications

### Basic Commands

**Deploy Stack**
```bash
docker stack deploy -c docker-compose-ray-head.yml <deployment_name>
```

**Monitor Stack**
```bash
# List all stacks
docker stack ls

# Check service status
docker service ps <deployment_name>

# View running containers
docker ps
```

### Troubleshooting
If services fail:
```bash
# View complete error messages
docker service ps deployment_name --no-trunc

# Check detailed service logs
docker service logs deployment_name --details
```

Note: Container names follow the pattern: `deployment_name.replica-number.uuid`