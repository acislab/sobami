# File name: Dockerfile
FROM vllm/vllm-openai:v0.7.0

# Set the working dir for the container to /serve_app
WORKDIR /app

# Copies the local `index.py` file into the WORKDIR
COPY /src/serve_app.py /app/
COPY /src/start.sh /app/
RUN chmod +x /app/start.sh
EXPOSE 8000

ENTRYPOINT []
# Start Ray and run the Python script
CMD ["/app/start.sh"]
