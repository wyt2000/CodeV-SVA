# llmkit_data

Modified vLLM server that supports configuring the number of GPUs used by each model instance.

## Installation

```bash
pip install -e .
```

## Usage

```python
python -m llmkit_data.cli.serve \
    --config $CONFIG_PATH \
    --log-dir $SERVER_LOG_DIR
```

See `examples/config.yaml` for more details.