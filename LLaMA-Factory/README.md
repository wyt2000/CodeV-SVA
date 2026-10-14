数据集没放进来，应该放在data/CodeV-SVA-dataset-83K-sva2wavedrom-qwen3p6-plus-diagram-wave2sva-self-verified-pass-images/和data/CodeV-SVA-dataset-83K-sva2wavedrom-qwen3p6-plus-diagram-wave2sva-self-verified-pass-training.jsonl

环境安装方式：

uv venv
source .venv/bin/activate
uv pip install -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cu128 --index-strategy unsafe-best-match
uv pip install -e .

用conda应该也可以

训练脚本在slurm