from typing import Dict, Optional, List
import logging
import os

from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import StreamingResponse, JSONResponse

from ray import serve

from vllm.engine.arg_utils import AsyncEngineArgs
from vllm.engine.async_llm_engine import AsyncLLMEngine
from vllm.entrypoints.openai.cli_args import make_arg_parser
from vllm.entrypoints.openai.protocol import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ErrorResponse,
)
from vllm.entrypoints.openai.serving_chat import OpenAIServingChat
from vllm.entrypoints.openai.serving_models import BaseModelPath, OpenAIServingModels
from vllm.utils import FlexibleArgumentParser
from vllm.entrypoints.logger import RequestLogger

logger = logging.getLogger("ray.serve")

app = FastAPI()

@serve.deployment(
    autoscaling_config={"max_replicas": 1},
    ray_actor_options={
        "runtime_env": {"pip": ["vllm==0.8.3"]}
    }
)
@serve.ingress(app)
class VLLMDeployment:
    def __init__(
        self,
        engine_args: AsyncEngineArgs,
        response_role: str,
        request_logger: Optional[RequestLogger] = None,
        chat_template: Optional[str] = None,
    ):
        logger.info(f"Starting with engine args: {engine_args}")
        self.engine_args = engine_args
        self.response_role = response_role
        self.request_logger = request_logger
        self.chat_template = chat_template
        self.openai_serving_chat = None
        if 'CUDA_VISIBLE_DEVICES' in os.environ:
            logger.info(f"Unsetting CUDA_VISIBLE_DEVICES (was {os.environ['CUDA_VISIBLE_DEVICES']})")
            del os.environ['CUDA_VISIBLE_DEVICES']
        self.engine = AsyncLLMEngine.from_engine_args(engine_args)

    @app.post("/v1/chat/completions")
    async def create_chat_completion(
        self, request: ChatCompletionRequest,   raw_request: Request
    ):
        """OpenAI-compatible HTTP endpoint.

        API reference:
            - https://docs.vllm.ai/en/latest/serving/openai_compatible_server.html
        """
        print('Incoming completion request...')
        if not self.openai_serving_chat:
            model_config = await self.engine.get_model_config()
            print('Model config, completion request...')
            # Determine the name of the served model for the OpenAI client.
            if self.engine_args.served_model_name is not None:
                served_model_names = self.engine_args.served_model_name
            else:
                served_model_names = [self.engine_args.model]
            base_model_paths = [
                BaseModelPath(name=name, model_path=self.engine_args.model)
                for name in served_model_names
            ]
            self.openai_serving_models = OpenAIServingModels(
                engine_client=self.engine,
                model_config=model_config,
                base_model_paths=base_model_paths,
            )
            self.openai_serving_chat = OpenAIServingChat(
                self.engine,
                model_config,
                self.openai_serving_models,
                self.response_role,
                request_logger=self.request_logger,
                chat_template=self.chat_template,
                chat_template_content_format=None,
            )
        logger.info(f"Request: {request}")
        generator = await self.openai_serving_chat.create_chat_completion(
            request, raw_request
        )
        if isinstance(generator, ErrorResponse):
            return JSONResponse(
                content=generator.model_dump(), status_code=generator.code
            )
        if request.stream:
            return StreamingResponse(content=generator, media_type="text/event-stream")
        else:
            assert isinstance(generator, ChatCompletionResponse)
            return JSONResponse(content=generator.model_dump())


def parse_vllm_args(cli_args: Dict[str, str]):
    """Parses vLLM args based on CLI inputs.

    Currently uses argparse because vLLM doesn't expose Python models for all of the
    config options we want to support.
    """
    arg_parser = FlexibleArgumentParser(
        description="vLLM OpenAI-Compatible RESTful API server."
    )

    parser = make_arg_parser(arg_parser)
    arg_strings = []
    for key, value in cli_args.items():
        arg_strings.extend([f"--{key}", str(value)])
    logger.info(arg_strings)
    parsed_args = parser.parse_args(args=arg_strings)
    return parsed_args


def build_app(cli_args: Dict[str, str]) -> serve.Application:
    """Builds the Serve app based on CLI arguments.

    See https://docs.vllm.ai/en/latest/serving/openai_compatible_server.html#command-line-arguments-for-the-server
    for the complete set of arguments.

    Supported engine arguments: https://docs.vllm.ai/en/latest/models/engine_args.html.
    """
    # Add these to cli_args if not present
    if "max_num_seqs" not in cli_args:
        cli_args["max_num_seqs"] = "64"
    if "max_num_batched_tokens" not in cli_args:
        cli_args["max_num_batched_tokens"] = "8192"
    
    parsed_args = parse_vllm_args(cli_args)
    engine_args = AsyncEngineArgs.from_cli_args(parsed_args)
    print(f'Parsed_args: {parsed_args}, Engine: {engine_args}')
    pg_bundles = [{"CPU": 1, "GPU": 1},{"CPU": 1, "GPU": 1}]

    return VLLMDeployment.options(
        placement_group_bundles=pg_bundles,
        placement_group_strategy="PACK"
    ).bind(
        engine_args,
        parsed_args.response_role,
        cli_args.get("request_logger"),
        parsed_args.chat_template,
    )

