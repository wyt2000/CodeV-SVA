import argparse
import socket
import logging
import os
import random
import signal
import subprocess
import sys
import time
from typing import List, Optional
import requests
import pathlib
import yaml
from collections import defaultdict
import traceback

from llmkit_data.utils.router import RouterApp
from llmkit_data.utils.parallel import allocate_gpu


def setup_logger():
    logger = logging.getLogger("router")
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "[Server (Python)] %(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


logger = setup_logger()


def is_port_available(port: int, host: str = "localhost") -> bool:
    try:
        # Create a socket object
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # Try to bind the socket to the port
            s.bind((host, port))
            # If successful, the port is available
            return True
    except OSError:
        # If binding fails, the port is already in use
        return False


def find_available_ports(host: str, base_port: int, count: int) -> List[int]:
    """Find consecutive available ports starting from base_port."""
    available_ports = []
    current_port = base_port + random.randint(100, 1000)

    while len(available_ports) < count:
        if is_port_available(current_port, host):
            available_ports.append(current_port)
        current_port += random.randint(100, 1000)

    return available_ports


def wait_for_server_health(
    host: str,
    port: int,
    timeout: int = 3600,
    http_path: Optional[str] = None,
    http_success_codes: Optional[list] = None,
) -> bool:
    """
    Wait for a server to become healthy by checking TCP connectivity and optionally an HTTP endpoint.

    Args:
        host (str): The server's hostname or IP address.
        port (int): The server's port.
        timeout (int): Maximum time to wait in seconds (default: 300).
        http_path (Optional[str]): The HTTP path to check (e.g., "/health"). If None, only TCP connectivity is checked.
        http_success_codes (Optional[list]): List of HTTP status codes considered successful (default: [200]).

    Returns:
        bool: True if the server is healthy, False otherwise.
    """
    start_time = time.time()
    http_success_codes = http_success_codes or [200]

    while time.time() - start_time < timeout:
        # Step 1: Check TCP connectivity
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(5)  # Set a timeout for the connection attempt
                sock.connect((host, port))
                # If TCP connection succeeds, proceed to HTTP check (if applicable)
                if http_path is None:
                    return True  # TCP connectivity is enough

                # Step 2: Check HTTP endpoint (if provided)
                url = f"http://{host}:{port}{http_path}"
                try:
                    response = requests.get(url, timeout=5)
                    if response.status_code in http_success_codes:
                        return True
                except requests.exceptions.RequestException:
                    pass  # HTTP check failed, retry
        except (socket.timeout, ConnectionRefusedError, OSError):
            pass  # TCP connection failed, retry

        time.sleep(1)  # Wait before retrying

    return False  # Timeout reached, server is not healthy


def run_server(command, cuda_devices, timestamp, log_dir, model, idx):
    """Start the server using subprocess.Popen."""

    env = os.environ.copy()
    env["CUDA_VISIBLE_DEVICES"] = ",".join(cuda_devices)

    model = model.replace('/', '_')
    stdout_file = pathlib.Path(log_dir, f"vllmserver_{model}_{idx}_stdout_{timestamp}.log")
    stderr_file = pathlib.Path(log_dir, f"vllmserver_{model}_{idx}_stderr_{timestamp}.log")

    # Open the log files in append mode
    stdout_log = open(stdout_file, "a")
    stderr_log = open(stderr_file, "a")

    process = subprocess.Popen(
        command,
        env=env,
        stdout=stdout_log,  # Redirect stdout to stdout_file
        stderr=stderr_log,  # Redirect stderr to stderr_file
        preexec_fn=os.setpgrp,  # Create a new process group in the subprocess
    )

    process.stdout_log = stdout_log
    process.stderr_log = stderr_log
    return process


def cleanup_processes(processes: List[subprocess.Popen]):
    """Terminate all server processes."""
    for process in processes:
        logger.info(f"Terminating process {process.pid}")
        process.stdout_log.close()
        process.stderr_log.close()
        process.terminate()
        try:
            process.wait(timeout=5)  # Wait for the process to terminate (with a timeout)
        except subprocess.TimeoutExpired:
            logger.warning(f"Process {process.pid} did not terminate gracefully. Forcefully killing it.")
            process.kill()  # Forcefully kill the process
            process.wait()  # Wait for the process to terminate
    logger.info("All processes terminated")

def get_gpu_allocation(config) -> dict[str, list[int]]:
    """Allocate GPU for all models."""

    # Calculate GPU count for each model
    total_required_gpus = 0
    gpu_count_map = {}
    for model_config in config["models"]:
        assert model_config["model"] not in gpu_count_map, f"Duplicated Model Name: {model_config['model']}"
        tensor_parallel_size   = model_config.get("tensor_parallel_size", 1)
        pipeline_parallel_size = model_config.get("pipeline_parallel_size", 1)
        data_parallel_size     = model_config.get("data_parallel_size", 1)
        required_gpus          = tensor_parallel_size * pipeline_parallel_size * data_parallel_size
        total_required_gpus    += required_gpus
        gpu_count_map[model_config["model"]] = required_gpus

    # Get total available GPU count 
    cuda_visible_devices = os.getenv("CUDA_VISIBLE_DEVICES", "")
    visible_gpus = (
        [gpu_id.strip() for gpu_id in cuda_visible_devices.split(",")]
        if cuda_visible_devices
        else []
    )
    assert len(visible_gpus) == total_required_gpus, (
        f"Number of visible GPUs ({len(visible_gpus)}) does not match the requirement ({total_required_gpus}). "
        f"CUDA_VISIBLE_DEVICES={cuda_visible_devices}"
    )
    logger.info(
        f"GPU check passed: {len(visible_gpus)} GPUs are visible and match the requirement ({total_required_gpus})."
    )

    # Allocate GPU for each model
    gpu_idx_map = defaultdict(list)
    idx = 0
    for model, count in gpu_count_map.items():
        for _ in range(count):
            gpu_idx_map[model].append(visible_gpus[idx])
            idx += 1
    return gpu_idx_map

def start_server_for_model(host: str,
                           router_port: str,
                           config: dict,
                           gpu_idx_list: list[int],
                           log_dir: str) -> list[str]:
    """Parse the config and start the server for each model."""

    # Parse llm_kit args
    model                  = config["model"]
    tensor_parallel_size   = config.get("tensor_parallel_size", 1)
    pipeline_parallel_size = config.get("pipeline_parallel_size", 1)
    data_parallel_size     = config.get("data_parallel_size", 1)
    random_seeds           = config.get("random_seeds", [])
    logger.info(f"##### {model}: Starting Server Begin #####")

    # Find available ports for workers
    worker_ports = find_available_ports(host, router_port, data_parallel_size)

    # Find optimal CUDA_VISIBLE_DEVICES for workers
    cuda_devices_lst = allocate_gpu(
        tensor_parallel_size * pipeline_parallel_size,
        gpu_idx_list
    )

    # Parse vllm args
    config = config["vllm"]
    for key in ["host", "port", "seed"]:
        assert key not in config, f"{key} should be set outside the vllm scope"

    # Add original args
    config['host'] = host
    config['tensor_parallel_size'] = tensor_parallel_size
    config['pipeline_parallel_size'] = pipeline_parallel_size

    # Set seeds if they are in config file
    random_seeds = [random_seeds[i] if i < len(random_seeds) else None for i in range(len(worker_ports))]

    # Start server processes using a simple for loop
    server_processes = []
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    for i, worker_port in enumerate(worker_ports):
        try:
            command = ["vllm", "serve", model]
            config['port'] = worker_port
            command.append("--trust-remote-code")
            for key, value in config.items():
                command.append(f"--{key.replace('_', '-')}")
                if not isinstance(value, bool):
                    command.append(str(value))
            if random_seeds[i] is not None:
                command.append(f"--seed")
                command.append(str(random_seeds[i]))

            cuda_devices = cuda_devices_lst[i]
            logger.info("Running command: {} on GPU {}".format(" ".join(command), " ".join(cuda_devices)))
            process = run_server(command, cuda_devices, timestamp, log_dir, model, i)
            server_processes.append(process)
            logger.info(f"Launched DP server #{i} process")
        except Exception as e:
            logger.error(
                f"Failed to launch server #{i} process on port {worker_port}: {e}"
            )
            traceback.print_exc()
            cleanup_processes(server_processes)
            sys.exit(1)

    # Set up signal handlers for cleanup
    signal.signal(signal.SIGINT, lambda sig, frame: cleanup_processes(server_processes))
    signal.signal(
        signal.SIGTERM, lambda sig, frame: cleanup_processes(server_processes)
    )
    signal.signal(
        signal.SIGQUIT, lambda sig, frame: cleanup_processes(server_processes)
    )

    # Update router args with worker URLs
    worker_info = [(host, port) for port in worker_ports]
    logger.info(f"##### {model}: Starting Server End #####")

    return worker_info, server_processes

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, default="config.yaml", help="Server configuration file")
    parser.add_argument("--log-dir", type=str, default=".", help="Directory to save logs")
    args = parser.parse_args()

    # Load yaml config, see examples/config.yaml
    with open(args.config) as f:
        config = yaml.safe_load(f)
    config = config['llm_kit']

    # Parse llm_kit args
    host                   = config.get("host", "0.0.0.0")
    router_port            = config.get("router_port", 8000)
    router_timeout         = config.get("router_timeout", 1000)
    log_dir                = args.log_dir

    # Start servers for all models
    gpu_idx_map = get_gpu_allocation(config)
    worker_info_map = {}
    server_processes = []
    for model_config in config["models"]:
        model = model_config["model"]
        worker_info, server_processes_per_model = start_server_for_model(
            host           = host,
            router_port    = router_port,
            config         = model_config,
            gpu_idx_list   = gpu_idx_map[model],
            log_dir        = log_dir
        )
        worker_info_map[model] = worker_info
        server_processes.extend(server_processes_per_model)
    
    # Wait for all servers to become healthy
    logger.info("Waiting for server...")
    for model, worker_info in worker_info_map.items():
        for host, port in worker_info:
            if not wait_for_server_health(host, port):
                logger.error(f"{model}: Server on {host}:{port} did not become healthy")
                cleanup_processes(server_processes)
                sys.exit(1)
            logger.info(f"{model}: Server on {host}:{port} is healthy!")

    # Start rounter
    try:
        router_app = RouterApp(worker_info_map, host, router_port, router_timeout)
        router_app.run()
    except Exception as e:
        logger.error(f"Exception in router: {e}")
    finally:
        cleanup_processes(server_processes)

if __name__ == "__main__":
    main()
