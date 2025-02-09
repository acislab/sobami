### Ray Serve Deployments
https://docs.ray.io/en/latest/serve/key-concepts.html

- The examples folder contains the Ray Serve deployment scripts for vLLM and ML models with Fast API
- Ray Serve support [modal composition](https://docs.ray.io/en/latest/serve/model_composition.html)
- Each deployment is a Serve Application and Ray supports [multiple application](https://docs.ray.io/en/latest/serve/multi-app.html) deployments as well

Each example contains the script to setup code for Serve Application, resource allocation and a start script. This all comes together with docker. 

To run a serve application, build the respective image and run the docker container

```bash
docker build . -t serve_app_name:latest
docker run --network host -v /home/nitingoyal/storage/tmp/ray:/tmp/ray -e RAY_ADDRESS=10.13.44.223:3002 serve_app_name:latest
```

### Monitoring:

- Ray serve application deployments could be monitored on the Ray Dashboard `http://sobami1.acis.ufl.edu:5678/#/serve`
- [Prometheus metrics](https://docs.ray.io/en/latest/cluster/metrics.html) have been enabled for the ray cluster and is accessible at `http://sobami1.acis.ufl.edu:9090`
- Additionally, we could connect Zabbix with Prometheus metrics server

