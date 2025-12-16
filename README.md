# CodeV-SVA: Training Specialized LLMs for Hardware Assertion Generation via RTL-Grounded Bidirectional Data Synthesis 

<div align="center"> 
  <a href="https://huggingface.co/wyt2000/CodeV-SVA-14B"><img src="https://img.shields.io/static/v1?label=Model&message=HuggingFace&color=yellow"></a> &ensp;
  <a href="https://github.com/wyt2000/CodeV-SVA"><img src="https://img.shields.io/static/v1?label=Code&message=Github&color=blue"></a> &ensp;
</div>

## Introduction

We introduce CodeV-SVA, a family of large language models designed to translate natural-language verification properties into SystemVerilog Assertions (SVAs).

Open-Source Plan:

- Model ✓
- Evaluation code ✓
- Paper
- Dataset
- Data synthesis and training code

## Models

| Model | Download |
| -------- | -------- |
|    CodeV-SVA-8B     |   [🤗HuggingFace](https://huggingface.co/wyt2000/CodeV-SVA-8B)    |
|    CodeV-SVA-no-think-8B     |   [🤗HuggingFace](https://huggingface.co/wyt2000/CodeV-SVA-no-think-8B)    |
|    CodeV-SVA-14B     |   [🤗HuggingFace](https://huggingface.co/wyt2000/CodeV-SVA-14B)    |


## Evaluation Results

We employ human experts to recheck [FVEval](https://github.com/NVlabs/FVEval) benchmark, correcting
or removing erroneous tests (see `SVAClient/datasets`). The evaluation results are shown below:

| Model                 |             | NL2SVA-Human |             |      |             | NL2SVA-Machine |             |
| :-------------------- | :---------: | :----------: | :---------: | ---- | :---------: | :------------: | :---------: |
|                       |   Func.@1   |   Func.@16   |  Func.@32   |      |   Func.@1   |    Func.@16    |  Func.@32   |
|                       |             |              |             |      |             |                |             |
| DeepSeek-R1-671B      | <u>74.6</u> |   **90.3**   | <u>90.4</u> |      |    81.0     |      93.3      |    94.3     |
| GPT-5                 |    71.8     | <u>90.2</u>  |  **92.7**   |      |    81.8     |      93.2      |    94.3     |
| DeepSeek-V3.1-671B    |    63.1     |     81.4     |    84.9     |      | <u>83.8</u> |      92.9      |    93.6     |
| GPT-4o                |    64.1     |     75.2     |    78.1     |      |    68.5     |      81.3      |    83.7     |
|                       |             |              |             |      |             |                |             |
| RTLCoder-DS-v1.1-6.7B |    25.9     |     58.8     |    65.8     |      |    21.7     |      54.8      |    60.8     |
| CodeV-R1-Qwen-7B      |    25.2     |     55.8     |    61.6     |      |    37.4     |      76.6      |    83.0     |
|                       |             |              |             |      |             |                |             |
| Qwen3-8B              |    32.3     |     71.6     |    74.0     |      |    46.1     |      88.0      |    90.5     |
| Qwen3-14B             |    61.6     |     86.1     |    87.7     |      |    75.3     |      92.7      |    94.3     |
|                       |             |              |             |      |             |                |             |
| SVACoder-no-think-8B  |    65.8     |     84.4     |    86.3     |      |    78.7     |      90.9      |    91.9     |
| SVACoder-8B           |    72.0     |     88.8     | <u>90.4</u> |      |    83.5     |    **96.3**    |  **97.2**   |
| SVACoder-14B          |  **75.8**   |     89.4     | <u>90.4</u> |      |  **84.0**   |  <u>94.9</u>   | <u>95.8</u> |

## Reproduction

### Evaluation

1. Install the formal verification tool Cadence JasperGold 2023.12.

2. Install the required Python dependencies.

```bash
pip install -r requirements.txt
pip install -e SVAClient
pip install -e llm-kit-data
```

3. Start the HTTP server for formal verification (see `SVAServer/README.md`).

4. Start the modified vLLM server for the high-efficiency inference of CodeV-SVA.

```bash
cd SVAClient
bash eval_local/start_vllm_server.sh
```

5. Use `SVAClient` for SVA generation and verification. 

```bash
python -m SVAClient.cli.main \
    --task nl2sva_human # {nl2sva_human, nl2sva_machine, nl2sva_human_no_rtl} \
    --config configs/nl2sva_human_local_template_pass_at_k.yaml
```

We start the verification server on a CPU-only machine and forward the verification results to the GPU machines via SSH ports. GPU scheduling is handled using Slurm. See `SVAClient/eval_local/*.sh` for more details.

6. Compute the `Func.@k` metric.

```bash
python ../Scripts/nl2sva_pass_at_k.py \
    --result-path $VERIFICATION_PATH \
    --n $NUM_SAMPLES
```

## Citation

```latex
@misc{CodeV-SVA,
    title={CodeV-SVA: Training Specialized LLMs for Hardware Assertion Generation via RTL-Grounded Bidirectional Data Synthesis}, 
    author={Yutong Wu and Chenrui Cao and Pengwei Jin and Di Huang and Rui Zhang and Xishan Zhang and Zidong Du and Qi Guo and Xing Hu},
    year={2025},
    howpublished={\url{https://huggingface.co/wyt2000/CodeV-SVA-14B}},
}
```