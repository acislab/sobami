# Choose a base Ray image matching your Ray version and CUDA requirements
FROM rayproject/ray:2.43.0-py312-gpu

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
# Keep if needed for Torch compilation
ENV TORCH_CUDA_ARCH_LIST="7.0;8.0"

WORKDIR /app

# Install Ray with LLM extras and necessary backend libraries
RUN pip install --no-cache-dir "ray[serve,llm,train,default,data]==2.43.0" \
    transformers \
    accelerate \
    torch \
    "xgrammar==0.1.18"

COPY /src/llm_serve.py /app/
COPY --chmod=755 /src/start.sh /app/
EXPOSE 8000

ENTRYPOINT []
CMD ["/app/start.sh"]
