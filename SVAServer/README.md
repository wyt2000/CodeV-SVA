# SVAServer

An HTTP server that wraps Candence JasperGold, used for formal verification of SVAs.

## Setup

Please correctly install **JasperGold 2023.12** first to ensure that the `jg` command can run properly.

```bash
# check Cadence Jasper is accessible globally
jg -no_gui
```

Start the server:

```bash
bash start_server.sh
```

## Usage

Send HTTP requests to `http://127.0.0.1:4422/$TASK`, see `test_server.py` for more details.

## Task

- equal: determine the functional equivalence between two SVAs
