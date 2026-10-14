#!/bin/bash

mkdir -p vllm_server_output
TIME=$(date "+%Y-%m-%d-%H-%M-%S")
SERVER_LOG_PATH="vllm_server_output/generation_${TIME}.log"
MODEL_PATH="${MODEL_PATH:-/path/to/CodeV-SVA-model.gguf}"

python -m llama_cpp.server \
    --port 2244 \
    --model "$MODEL_PATH" \
    --n_gpu_layers 999 \
    --n_ctx 32768 \
    --cache False \
    > $SERVER_LOG_PATH 2>&1 &

