#!/bin/bash

# Function to handle SIGTERM
cleanup() {
  echo "Received SIGTERM, shutting down serve..."
  serve shutdown
  echo "Serve shutdown complete."
  exit 0
}

# Trap SIGTERM signal and call the cleanup function
trap cleanup SIGTERM

# Run the serve command in the background
serve run serve:build_app \
  model="meta-llama/Llama-3.1-8B-Instruct" \
  dtype=half \
  gpu_memory_utilization=0.90 \
  tensor_parallel_size=2 \
  pipeline_parallel_size=1 \
  max_model_len=2048 \
  max_num_seqs=64 \
  max_num_batched_tokens=8192 \
  guided_decoding_backend="xgrammar" &

# Wait for the background process to finish or for a signal
wait $!

cleanup
