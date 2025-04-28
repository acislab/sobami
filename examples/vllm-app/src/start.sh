#!/bin/bash

serve run llm_serve:build_app \
  model="meta-llama/Llama-3.1-8B-Instruct" \
  dtype=half \
  gpu_memory_utilization=0.90 \
  enable_chunked_prefill=false \
  tensor_parallel_size=2 \
  max_model_len=2048 \
  max_num_seqs=64 \
  max_num_batched_tokens=8192 \
  guided_decoding_backend="xgrammar"
