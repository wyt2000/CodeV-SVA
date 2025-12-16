MODEL_NAME=$1
MAX_TOKENS=$2
export NUM_SAMPLES=$3
GPU_ID=$4

PROBLEM_NAME="nl2sva_human"
TEMPLATE_PATH="configs/${PROBLEM_NAME}_local_no_rtl_template_pass_at_k.yaml"
RESULT_NAME="${PROBLEM_NAME}_${MODEL_NAME}_no_rtl_pass_at_k"
export CONFIG_PATH="config_records/${RESULT_NAME}.yaml"
export GENERATION_PATH="results/${RESULT_NAME}_generation.jsonl"
export VERIFICATION_PATH="results/${RESULT_NAME}_verification.jsonl"
export MODEL_PATH="/share/collab/codemodel/sva/models/${MODEL_NAME}/"

mkdir -p config_records

python -m SVAClient.cli.add_config \
  --template-path $TEMPLATE_PATH \
  --save-path $CONFIG_PATH  \
  --model-path $MODEL_PATH \
  --tokenizer-path $MODEL_PATH \
  --generation-path $GENERATION_PATH \
  --verification-path $VERIFICATION_PATH \
  --max-tokens $MAX_TOKENS \
  --num-samples $NUM_SAMPLES

submit eval_local/human_no_rtl.slurm $GPU_ID