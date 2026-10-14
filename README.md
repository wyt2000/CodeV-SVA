# CodeV-SVA: Training Specialized LLMs for Hardware Assertion Generation via RTL-Grounded Bidirectional Data Synthesis

<div align="center"> 
  <a href="https://huggingface.co/wyt2000/CodeV-SVA-14B"><img src="https://img.shields.io/static/v1?label=Model&message=HuggingFace&color=yellow"></a> &ensp;
  <a href="https://huggingface.co/datasets/wyt2000/CodeV-SVA-datasets"><img src="https://img.shields.io/static/v1?label=Dataset&message=HuggingFace&color=Red"></a> &ensp;
  <a href="https://github.com/wyt2000/CodeV-SVA"><img src="https://img.shields.io/static/v1?label=Code&message=Github&color=blue"></a> &ensp;
</div>

## Introduction

CodeV-SVA is a family of large language models designed to translate natural-language verification properties into SystemVerilog Assertions (SVAs). This repository provides the model-training framework, evaluation client, formal-verification server, data utilities, and metric scripts required for the complete CodeV-SVA workflow.

Open-source plan:

- Model ✓
- Evaluation code ✓
- Paper ✓
- Dataset ✓
- Data synthesis and training code ✓

## Repository structure

| Directory | Description |
| --- | --- |
| `LLaMA-Factory/` | Model training and fine-tuning framework. It contains training configurations, dataset registration, distributed training scripts, Docker files, and tests. CodeV-SVA training examples are under `examples/train_full/`, and cluster job examples are under `slurm/`. |
| `SVAClient/` | Client-side SVA workflows. It builds prompts, queries local or remote language models, requests formal verification, caches results, and runs tasks such as NL2SVA and Wave2SVA. |
| `SVAServer/` | HTTP formal-verification service. It wraps JasperGold-based flows and exposes syntax, equivalence, coverage, and testbench verification endpoints. |
| `Scripts/` | Standalone evaluation utilities, including the `Func.@k`/pass@k metric script. |

See the README and configuration files inside each component for more detailed usage.

## Models

| Model | Download |
| -------- | -------- |
|    CodeV-SVA-8B              |   [🤗HuggingFace](https://huggingface.co/wyt2000/CodeV-SVA-8B)             |
|    CodeV-SVA-no-think-8B     |   [🤗HuggingFace](https://huggingface.co/wyt2000/CodeV-SVA-no-think-8B)    |
|    CodeV-SVA-14B             |   [🤗HuggingFace](https://huggingface.co/wyt2000/CodeV-SVA-14B)            |
|    CodeV-SVA-VL-9B           |   [🤗HuggingFace](https://huggingface.co/wyt2000/CodeV-SVA-VL-9B)          |
|    CodeV-SVA-VL-27B          |   [🤗HuggingFace](https://huggingface.co/wyt2000/CodeV-SVA-VL-27B)         |

## Evaluation results

We evaluated the CodeV-SVA series on [FVEval](https://huggingface.co/datasets/wyt2000/FVEval-Verified), an NL2SVA benchmark manually reviewed and corrected by human experts, and evaluated the CodeV-SVA-VL series on [Wave2SVA](https://huggingface.co/datasets/wyt2000/Wave2SVA).

| Model | NL2SVA-Human Func.@1 | NL2SVA-Human Func.@16 | NL2SVA-Human Func.@32 | NL2SVA-Machine Func.@1 | NL2SVA-Machine Func.@16 | NL2SVA-Machine Func.@32 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| DeepSeek-R1-671B | <u>74.6</u> | **90.3** | <u>90.4</u> | 81.0 | 93.3 | 94.3 |
| GPT-5 | 71.8 | <u>90.2</u> | **92.7** | 81.8 | 93.2 | 94.3 |
| DeepSeek-V3.1-671B | 63.1 | 81.4 | 84.9 | <u>83.8</u> | 92.9 | 93.6 |
| GPT-4o | 64.1 | 75.2 | 78.1 | 68.5 | 81.3 | 83.7 |
| RTLCoder-DS-v1.1-6.7B | 25.9 | 58.8 | 65.8 | 21.7 | 54.8 | 60.8 |
| CodeV-R1-Qwen-7B | 25.2 | 55.8 | 61.6 | 37.4 | 76.6 | 83.0 |
| Qwen3-8B | 32.3 | 71.6 | 74.0 | 46.1 | 88.0 | 90.5 |
| Qwen3-14B | 61.6 | 86.1 | 87.7 | 75.3 | 92.7 | 94.3 |
| CodeV-SVA-no-think-8B | 65.8 | 84.4 | 86.3 | 78.7 | 90.9 | 91.9 |
| CodeV-SVA-8B | 72.0 | 88.8 | <u>90.4</u> | 83.5 | **96.3** | **97.2** |
| CodeV-SVA-14B | **75.8** | 89.4 | <u>90.4</u> | **84.0** | <u>94.9</u> | <u>95.8</u> |



| Model                  |                | Wave2SVA         |             |
| :--------------------  | :---------:    | :----------:     | :---------: |
|                        |   Func.@1      |   Func.@16       |  Func.@32   |
|                        |                |                  |             |
| Qwen3.6-Plus           |    53.8        |     **89.4**     |  **94.0**   |
| GPT-5.4                |    <u>53.9</u> |     77.4         |    84.0     |
| GLM-5V                 |    50.9        |     82.8         |    88.0     |
|                        |                |                  |             |
| Kimi-K2.7-Code-1T-A32B |    49.6        |     <u>86.4</u>  |    90.0     |
| GLM-4.6V-106B-A12B     |    26.1        |     66.3         |    76.0     |
|                        |                |                  |             |
| Qwen3.5-8B             |    16.5        |     65.2         |    70.0     |
| Qwen3.5-27B            |    25.4        |     68.3         |    74.0     |
|                        |                |                  |             |
| CodeV-SVA-VL-9B        |    51.9        |     79.4         |    82.0     |
| CodeV-SVA-VL-27B       |    **54.9**    |     85.5         |    <u>92.0</u>     |

## Reproduction

### Evaluation

1. Install Cadence JasperGold 2023.12 and confirm that the `jg` command is available.

2. Install the required Python dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e ./SVAClient
pip install -e ./llm-kit-data
pip install -r ./SVAServer/requirements.txt
```

3. Start the formal-verification HTTP server. See `SVAServer/README.md` for details.

```bash
cd SVAServer
bash start_server.sh
```

4. Start the modified vLLM server for high-efficiency CodeV-SVA inference:

```bash
cd SVAClient
bash eval_local/start_vllm_server.sh
```

5. Use `SVAClient` for SVA generation and verification:

```bash
cd SVAClient
python -m SVAClient.cli.main \
  --task nl2sva_human \
  --config configs/nl2sva_human_local_template_pass_at_k.yaml
```

Available evaluation tasks include `nl2sva_human`, `nl2sva_machine`, and `nl2sva_human_no_rtl`. The verification server can run on a CPU-only machine, while model inference can run on GPU machines. The examples under `SVAClient/eval_local/` include Slurm and SSH-forwarding workflows that should be adapted to the local environment.

6. Compute the `Func.@k` metric:

```bash
python Scripts/nl2sva_pass_at_k.py \
  --result-path "$VERIFICATION_PATH" \
  --n "$NUM_SAMPLES"
```

### Model training

Install the training environment:

```bash
cd LLaMA-Factory
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt \
  --extra-index-url https://download.pytorch.org/whl/cu128 \
  --index-strategy unsafe-best-match
uv pip install -e .
```

Place training data under `LLaMA-Factory/data/` and register it in the dataset configuration. A training example can then be launched with:

```bash
llamafactory-cli train examples/train_full/sft_qwen3p5_9B_0407.yaml
```

For multi-node or scheduled training, adapt the examples under `LLaMA-Factory/slurm/` to the local scheduler, CUDA environment, model location, and storage layout.

## Citation

```bibtex
@misc{wu2026qimengcodevsvatrainingspecializedllms,
      title={QiMeng-CodeV-SVA: Training Specialized LLMs for Hardware Assertion Generation via RTL-Grounded Bidirectional Data Synthesis}, 
      author={Yutong Wu and Chenrui Cao and Pengwei Jin and Di Huang and Rui Zhang and Xishan Zhang and Zidong Du and Qi Guo and Xing Hu},
      year={2026},
      eprint={2603.14239},
      archivePrefix={arXiv},
      primaryClass={cs.CL},
      url={https://arxiv.org/abs/2603.14239}, 
}
```
