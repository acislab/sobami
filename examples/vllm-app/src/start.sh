#!/bin/bash

serve run ml_serve:build_app model="meta-llama/Llama-3.1-8B-Instruct" dtype=half gpu_memory_utilization=0.95 enable_chunked_prefill=false pipeline_parallel_size=2 max_model_len=2048