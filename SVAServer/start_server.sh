#!/bin/bash

mkdir -p server_output
TIME=$(date "+%Y-%m-%d-%H-%M-%S")
SERVER_LOG_PATH="server_output/server_${TIME}.log"
CONFIG_PATH="../SVAClient/configs/nl2sva_human_local_template_pass_at_k.yaml"

python Server.py \
    --config $CONFIG_PATH \
    > $SERVER_LOG_PATH 2>&1 &
