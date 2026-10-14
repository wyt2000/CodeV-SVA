#!/bin/bash

mkdir -p vllm_server_output
TIME=$(date "+%Y-%m-%d-%H-%M-%S")
SERVER_LOG_PATH="vllm_server_output/generation_${TIME}.log"

SERVER_LOG_DIR="vllm_server_output/vllm_server_${TIME}"
mkdir -p $SERVER_LOG_DIR

python -m llmkit_data.cli.serve \
    --config $EVAL_CONFIG_PATH \
    --log-dir $SERVER_LOG_DIR \
    > $SERVER_LOG_PATH 2>&1 &

