# SVAClient

A high-efficiency client for both LLM queries and formal verification of SVAs.

## Installation

```bash
pip install -e .
```

## Usage

```python
python -m SVAClient.cli.main \
    --task $TASK \
    --config $CONFIG_PATH
```

## Task

- nl2sva_human
- nl2sva_machine
- nl2sva_human_no_rtl

