MODEL_NAME=$1
MAX_TOKENS=$2
GPU_ID=$3

PROBLEM_NAME="nl2sva_machine"
TEMPLATE_PATH="configs/${PROBLEM_NAME}_local_template.yaml"
RESULT_NAME="${PROBLEM_NAME}_${MODEL_NAME}"
export CONFIG_PATH="config_records/${RESULT_NAME}.yaml"
export GENERATION_PATH="results/${RESULT_NAME}_generation.jsonl"
export VERIFICATION_PATH="results/${RESULT_NAME}_verification.jsonl"
export MODEL_ROOT="${MODEL_ROOT:-/path/to/models}"
export MODEL_PATH="${MODEL_ROOT}/${MODEL_NAME}"

mkdir -p config_records

python -m SVAClient.cli.add_config \
  --template-path $TEMPLATE_PATH \
  --save-path $CONFIG_PATH  \
  --model-path $MODEL_PATH \
  --tokenizer-path $MODEL_PATH \
  --generation-path $GENERATION_PATH \
  --verification-path $VERIFICATION_PATH \
  --max-tokens $MAX_TOKENS

submit eval_local/machine.slurm $GPU_ID
