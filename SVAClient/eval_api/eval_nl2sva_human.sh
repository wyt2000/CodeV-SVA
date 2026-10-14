MODEL_NAME=$1
MAX_TOKENS=$2
PROBLEM_NAME="nl2sva_human"
TEMPLATE_PATH="configs/${PROBLEM_NAME}_template.yaml"
RESULT_NAME="${PROBLEM_NAME}_${MODEL_NAME}"
CONFIG_PATH="config_records/${RESULT_NAME}.yaml"
GENERATION_PATH="results/${RESULT_NAME}_generation.jsonl"
VERIFICATION_PATH="results/${RESULT_NAME}_verification.jsonl"

mkdir -p config_records

python -m SVAClient.cli.add_config \
  --template-path $TEMPLATE_PATH \
  --save-path $CONFIG_PATH  \
  --model-path $MODEL_NAME \
  --generation-path $GENERATION_PATH \
  --verification-path $VERIFICATION_PATH \
  --max-tokens $MAX_TOKENS

python -m SVAClient.cli.main --task nl2sva_human --config $CONFIG_PATH
python ../Scripts/nl2sva_pass_at_k.py --result-path $VERIFICATION_PATH