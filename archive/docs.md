# vLLM Installation Guide

## Pre-requisites

- **OS**: Linux
- **Python**: 3.9-3.12
- **GPU**: Compute capability of 7.0 or higher
- **CUDA**: 12.1 (This might change as maintainers compile the vLLM)

## Installation

`setup.sh` will validate the GPU and CUDA versions and dependencies to support vLLM deployment.

```bash
chmod +x setup_node.sh
sudo bash setup_node.sh
```

### Hardware and Communication Sanity Check

vLLM provides a sanity check to ensure everything is set up correctly.
<!-- TODO: understand why sanity.py does not work for our current setup. -->


### Notes and Troubleshooting

1. **Ray Storage Configuration**: Ray requires less than 90% disk utilization. Since Sobami 2 is running short of disk space, we've mounted a dedicated storage directory (`~/storage/tmp/ray/`) to handle this. Alternatively, you can configure a object spill-over directory through Ray configurations when starting the head node. [More details](https://docs.ray.io/en/master/ray-core/objects/object-spilling.html#cluster-mode)

2. **Server Stability**: The `--enable-chunked-prefill=False` parameter is crucial to prevent server crashes until it is fixed. [Related issue](https://github.com/vllm-project/vllm/issues/8024)

3. **GCS Issues**: There's a known issue when using Sobami 1 as the head node, related to Global Control Service (GCS). The server will not start. [Issue details](https://github.com/ray-project/ray/issues/24920) | [GCS documentation](https://docs.ray.io/en/master/cluster/kubernetes/user-guides/kuberay-gcs-ft.html#kuberay-gcs-ft)

4. **Docker Image Versions**: For the latest vLLM docker images, check:
   - [Release information](https://github.com/vllm-project/vllm/issues/721)
   - [Docker Hub tags](https://hub.docker.com/r/vllm/vllm-openai/tags)

### Access Points
- Ray Dashboard: sobami2.acis.ufl.edu:5678
- OpenAI Server: sobami2.acis.ufl.edu:8000

## Monitoring and Logging

### Cluster

- Ray provides a cluster dashboard which can be accessed at [Ray Dashboard](http://sobami2.acis.ufl.edu:5678). The Ray dashboard provides information about the nodes available in the cluster, including available resources and the number of tasks that are currently running.

- However, Ray does not display cluster metrics information. To access the cluster metrics, we need to set up Prometheus. Here is how to do it: [Ray Cluster Metrics Setup](https://docs.ray.io/en/latest/cluster/metrics.html).

### vLLM Server

- The vLLM server also exposes Prometheus metrics. The documentation for this can be accessed [here](https://docs.vllm.ai/en/latest/serving/metrics.html).

## Observations

These are some of the things I observed while setting up the vLLM cluster.

### vLLM Memory Usage

With the repeated deployments of LLMs of various sizes, I noticed a couple of things:

1. Even the smaller models occupy most of the available GPU memory (up to gpu-utilization %). For instance, in the snapshot of logs when I loaded the `meta-llama/Llama-3.1-8B-Instruct` model onto the cluster below:

    <figure style="width: 100%; text-align: center;">
        <img src="./static/image-1.png" alt="Memory allocation to model and KV cache by vLLM" style="max-width: 100%; height: auto;">
        <figcaption style="text-align: center;">Figure 1: Memory allocation to model and KV cache by vLLM</figcaption>
    </figure>

    Here, we can see that vLLM loads the model weights only in 5.07GiB and reserves the rest for KV cache.

2. But, how much space is needed for KV cache to obtain decent performance out of it? To see the effect on inference, I loaded larger models which take up more memory and observed the performance.
    <!-- TODO: Figure out how to measure actual cache usage vs reserved cache space. -->

3. For smaller models with model weights < 10GiB, I was expecting vLLM to utilize only a single GPU instance, but all of the GPUs were being used. In the diagram above, we can also see that the model is loaded to all three of our GPUs. This is because of the `pipeline-parallel_size=3` argument. vLLM uses this pipeline parallelism to split the model layers across multiple GPUs. This is done to reduce the memory usage on a single GPU and to increase the throughput of the model. But for smaller models, this might not be necessary, and rather we could replicate the model deployment to enable even higher throughput. This, I believe, is done with Ray[Serve] scaling configurations.

    <!-- TODO: While it is easier to set up Ray[Serve] with a custom API server, I have not yet figured out how to do it for vLLM's OpenAI API server. This will also enable us to monitor the LLM serve deployments over the cluster through the Ray dashboard. -->

## References

- [Installation Guide](https://docs.vllm.ai/en/stable/getting_started/installation.html)
- [Ray Cluster Details](https://docs.ray.io/en/latest/cluster/key-concepts.html#ray-cluster)

## TODO

- [ ] Implement Prometheus server to ingest both vLLM and Ray logs
- [ ] Check out vLLM's function calling abilities - Here is an example of tool calling: [OpenAI Chat Completion Client with Tools](https://docs.vllm.ai/en/stable/getting_started/examples/openai_chat_completion_client_with_tools.html)
- [ ] Set up vLLM deployment with Ray[Serve] LLM performance monitoring: [vLLM Inference](https://modal.com/docs/examples/vllm_inference)
- [ ] Another way is to use KubeAI to deploy the model: [KubeAI Installation](https://www.kubeai.org/installation/any/)
- [ ] Check the network security for Docker containers: [Docker Network Bridge](https://docs.docker.com/network/bridge/)

```bash
(dev-nlp) (base) nitingoyal@sobami2:~/nitingoyal/cluster$ sudo docker info | grep -i runtime
 Runtimes: io.containerd.runc.v2 nvidia runc
 Default Runtime: runc
WARNING: bridge-nf-call-iptables is disabled
WARNING: bridge-nf-call-ip6tables is disabled
```
