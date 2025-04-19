import os
from typing import Dict
from ray import serve
from dotenv import load_dotenv
# from ray.serve.llm import LLMServer, LLMConfig, LLMRouter
from ray.serve.llm import LLMConfig, build_openai_app

# Documentation:
# https://docs.ray.io/en/latest/serve/llm/serving-llms.html
def parse_cli_args(cli_args: Dict[str, str]) -> Dict[str, str]:
    # disable_chunked_prefill for V100s: https://github.com/kaito-project/kaito/pull/971
    defaults = {
        "tensor_parallel_size": "2",
        "gpu_memory_utilization": "0.90",
        "max_model_len": "2048",
        "max_num_seqs": "64",
        "max_num_batched_tokens": "8192",
        "dtype": "half",
        "enable_chunked_prefill": "false"
    }
    return {**defaults, **cli_args}

# Related github issues: https://github.com/ray-project/ray/issues/51242
def build_app(cli_args: Dict[str, str]) -> serve.Application:
    args = parse_cli_args(cli_args)

    load_dotenv('.serve.env')
    HF_TOKEN = os.environ.get("HF_TOKEN")

    llm_config_dict = {
        "model_loading_config": {
            "model_id": args.get("model", "meta-llama/Llama-3.1-8B-Instruct"),
            "model_source": "meta-llama/Llama-3.1-8B-Instruct",
        },
        "engine_kwargs": {
            "tensor_parallel_size": int(args["tensor_parallel_size"]),
            "pipeline_parallel_size": int(args.get("pipeline_parallel_size", "1")),
            "gpu_memory_utilization": float(args["gpu_memory_utilization"]),
            "max_model_len": int(args["max_model_len"]),
            "max_num_seqs": int(args["max_num_seqs"]),
            "max_num_batched_tokens": int(args["max_num_batched_tokens"]),
            "dtype": args["dtype"],
            "enable_chunked_prefill": args["enable_chunked_prefill"].lower() == "true",
        },
        "deployment_config": {
            "ray_actor_options": {},
            "autoscaling_config": {
                "min_replicas": 1,
                "max_replicas": 1
            }
        },
        "accelerator_type": "V100",
        "runtime_env": {
            "pip": ["httpx", "ray[llm,serve]==2.44.1", "vllm==0.7.2"],
            "env_vars": {
                "USE_VLLM_V1": "0",
                "HF_TOKEN": HF_TOKEN,
                "TRITON_DISABLE":"mma,cutlass"
            }
        }
    }
    configs = LLMConfig(**llm_config_dict)

    # Approach - 1: LLMRouter can be used to manage multiple LLM deployments
    # bundles=[
    #         {"CPU": 1, "GPU": 1} 
    #         for _ in range(int(args["tensor_parallel_size"]))
    #     ]

    # deployment = LLMServer.as_deployment(
    #     configs.get_serve_options(name_prefix="vLLM:"),
    # ).options(
    #     placement_group_bundles=bundles,
    #     placement_group_strategy="PACK"
    # ).bind(configs)

    # Unable to startup the OpenAI Server
    # Finally, raised issue with maintainer T-T
    # https://github.com/ray-project/ray/issues/51242#issuecomment-2806786244
    # app = LLMRouter.as_deployment().bind(llm_deployments=[deployment])
    
    # Approach - 2: manages the llmconfig and llmrouter
    app = build_openai_app({"llm_configs": [configs]})
    
    return app
