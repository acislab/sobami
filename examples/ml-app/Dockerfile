# Use the vLLM base image
FROM vllm/vllm-openai:v0.7.0

# Set the working directory
WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY /requirements.txt .
RUN pip3.12 install -r requirements.txt
RUN pip list

COPY /ml_serve.py .

COPY /start.sh .
RUN chmod +x ./start.sh

EXPOSE 8001

ENTRYPOINT []
CMD ["/app/start.sh"]
