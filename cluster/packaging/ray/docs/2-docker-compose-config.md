## Environment Variable Interpolation in Docker Stack

### Generate `docker compose` Configuration
```bash
docker compose --env-file .env config > docker-compose-configured.yml
```
docker compose by default look for `docker-compose.yml` in the current folder.

### Modify Generated YAML
Remove from generated file:
```yaml
name: ray    # Remove this line
services:
  ray-head:
    command:
      - -c
      - ray start -- ...
```

### Deploy Stack
```bash
sudo docker stack deploy -c docker-compose-configured.yml cluster_name
```

Note: This is a workaround solution I found as Docker Stack doesn't directly support environment variable interpolation.