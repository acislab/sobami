'''
References: 

MLOps Talk: https://github.com/dmatrix/ray-core-serve-tutorial-mlops/blob/main/ex_08_ray_serve_end_to_end.ipynb
Ray cluster dependency management docs: https://docs.ray.io/en/latest/ray-core/handling-dependencies.html#runtime-environments


'''

import torch
from PIL import Image
import numpy as np
from io import BytesIO
from fastapi.responses import Response
from fastapi import FastAPI

import ray
from ray import serve
from ray.serve.handle import DeploymentHandle

runtime_env = {"pip": ["ultralytics"]}

ray.init(runtime_env=runtime_env)

serve.start(http_options={"host": "0.0.0.0", "port": "8001"})

app = FastAPI()

@serve.deployment(
    autoscaling_config={
        "max_replicas": 1,
    }
)
@serve.ingress(app)
class APIIngress:
    def __init__(self, object_detection_handle: DeploymentHandle):
        self.handle = object_detection_handle

    @app.get(
        "/detect",
        responses={200: {"content": {"image/jpeg": {}}}},
        response_class=Response,
    )
    async def detect(self, image_url: str):
        image = await self.handle.detect.remote(image_url)
        file_stream = BytesIO()
        image.save(file_stream, "jpeg")
        return Response(content=file_stream.getvalue(), media_type="image/jpeg")


@serve.deployment(
    ray_actor_options={"num_gpus": 1},
    autoscaling_config={"min_replicas": 1},
)
class ObjectDetection:
    def __init__(self):
        self.model = torch.hub.load("ultralytics/yolov5", "yolov5s")
        self.model.cuda()
        self.model.to(torch.device(0))

    def detect(self, image_url: str):
        result_im = self.model(image_url)
        return Image.fromarray(result_im.render()[0].astype(np.uint8))

entrypoint = APIIngress.bind(
    ObjectDetection.options(
        placement_group_bundles=[{"CPU": 1, "GPU": 1}], 
        placement_group_strategy="SPREAD"
    ).bind()
)

