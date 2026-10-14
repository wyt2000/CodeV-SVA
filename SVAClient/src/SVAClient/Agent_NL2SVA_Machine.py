import concurrent.futures
import json
import logging
import concurrent
import yaml
import random
import traceback
import os
from collections import defaultdict

from SVAClient import Utils
from SVAClient.Client import LLMClient, VerifierClient 
from SVAClient import Prompter

class Agent:
    
    def __init__(self,
                config: dict,
                rank: int = -1,
                num_nodes: int = -1,
                generation_path: str | None = None,
                verification_path: str | None = None):
        with open(config) as f:
            config = yaml.safe_load(f)
        logging.warning(f'Config: {config}')
        logging.warning(f'Rank: {rank}, num_nodes: {num_nodes}')
        assert (rank == -1 and num_nodes == -1) or (rank >= 0 and num_nodes > 0 and rank < num_nodes)
        self.rank                = rank
        self.num_nodes           = num_nodes
        self.generate_only       = config.get('generate_only', False)
        self.verify_only         = config.get('verify_only', False)
        self.use_cache           = config.get('use_cache', False)
        self.generation_path     = None
        self.generation_cache    = defaultdict(list)
        self.verification_path   = None
        self.verification_cache  = set()
        assert not (self.generate_only and self.verify_only)

        if not self.verify_only:
            self.LLMClient = LLMClient(config=config["llm_kit"])
            self.LLMClient.wait_until_connected()
            self.generation_path = generation_path if generation_path else config["agent"]["generation"]["path"]
            if self.use_cache and os.path.exists(self.generation_path):
                self.generation_cache = self.load_generation_cache(self.generation_path)
            if rank != -1: self.generation_path = f"{self.generation_path}.{rank}"

        if not self.generate_only:
            self.verifierClient = VerifierClient(
                host = config["verifier"]["host"],
                port = config["verifier"]["port"]
            )
            self.verifierClient.wait_until_connected()
            self.verification_path = verification_path if verification_path else config["agent"]["verification"]["path"]
            if self.use_cache and os.path.exists(self.verification_path):
                self.verification_cache = self.load_verification_cache(self.verification_path)
            if rank != -1: self.verification_path = f"{self.verification_path}.{rank}"

        if seed := config.get("random_seed"): random.seed(seed)
        self.config = config["agent"]

    def load_generation_cache(self, path):
        cache = defaultdict(list)
        with open(path) as f:
            for data in f:
                data = json.loads(data)
                cache[data['name']].append(data)
        return cache

    def load_verification_cache(self, path):
        cache = set()
        with open(path) as f:
            for data in f:
                data = json.loads(data)
                cache.add((data["name"], data['sva']))
        return cache

    def load_dataset(self):
        # Load dataset
        dataset = []
        with open(self.config["problem"]["path"]) as f:
            for data in f.readlines():
                data = json.loads(data)
                dataset.append(data)

        if self.rank == -1:
            return dataset

        # Select the rank-th part of the dataset
        n = len(dataset)
        base_size = n // self.num_nodes
        remainder = n % self.num_nodes
        if self.rank < remainder:
            start = self.rank * (base_size + 1)
            end = start + base_size + 1
        else:
            start = self.rank * base_size + remainder
            end = start + base_size
        dataset = dataset[start:end]
        logging.warning(f'Total data count: {len(dataset)}')
        return dataset

    def solve(self):
        # Solve problems in each batch
        dataset        = self.load_dataset()
        batch_size     = self.config["problem"]["batch_size"]
        if batch_size == -1:
            batch_size = len(dataset)
        generation_f   = open(self.generation_path, 'w' if not self.generation_cache else 'a') if not self.verify_only else None
        verification_f = open(self.verification_path, 'w' if not self.verification_cache else 'a') if not self.generate_only else None
        for i in range(0, len(dataset), batch_size):
            dataset_batch = dataset[i:i + batch_size]
            self._solve_impl(dataset_batch, generation_f, verification_f)
            logging.warning(f'Total Problem: {min(i + batch_size, len(dataset))} / {len(dataset)} completed!')
        if generation_f:   generation_f.close()
        if verification_f: verification_f.close()

    def _solve_impl(self, dataset: list[dict[str, str]], generation_f, verification_f):
        # Set executors
        generation_executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.config["generation"]["max_workers"]) if not self.verify_only else None
        verification_executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.config["verification"]["max_workers"]) if not self.generate_only else None

        verification_futures = {}
        generations_to_verify = []

        def verify_generations():
            nonlocal generations_to_verify
            data_list = generations_to_verify
            verification_future = verification_executor.submit(self.verify, data_list)
            verification_futures[verification_future] = generations_to_verify
            generations_to_verify = []

        if self.verify_only:
            # Get verify proofs in the dataset
            for data in dataset:
                # Load and save cache
                if self.use_cache:
                    if (data["name"], data["sva"]) in self.verification_cache: continue
                    self.verification_cache.add((data["name"], data["sva"]))
                generations_to_verify.append(data)
                if len(generations_to_verify) == self.config["verification"]["batch_size"]:
                    verify_generations()
            if generations_to_verify:
                verify_generations()
        else:
            # Caculate completion times for each batch
            total_samples = self.config["problem"]["num_samples"]
            generation_batch_size = self.config["generation"]["batch_size"]
            # Generate
            generation_futures = {} 
            problems_to_generate = []

            def generate_for_problems():
                nonlocal problems_to_generate
                generation_future = generation_executor.submit(self.generate, problems_to_generate)
                generation_futures[generation_future] = problems_to_generate
                problems_to_generate = []

            # Submit generation task considering cache
            for i, data in enumerate(dataset):
                for j in range(total_samples - len(self.generation_cache[data["name"]])):
                    problems_to_generate.append(data)
                    if len(problems_to_generate) == generation_batch_size:
                        generate_for_problems()
            if problems_to_generate:
                generate_for_problems()
            logging.warning(f'Total Generation Tasks: {len(generation_futures)}')

            # Get generation results then verify
            for i, generation_future in enumerate(concurrent.futures.as_completed(generation_futures)):
                try:
                    responses = generation_future.result(timeout=self.config["generation"]["timeout"])
                except concurrent.futures.TimeoutError as err:
                    logging.error(f'Timeout in generation!')
                except Exception as err:
                    logging.error(f'Error in generation: {err}')
                    logging.error(f'{traceback.format_exc()}')
                else:
                    data_batch = generation_futures[generation_future]
                    for response, data in zip(responses, data_batch):
                        generation_result = data | response
                        generation_f.write(json.dumps(
                            generation_result,
                            ensure_ascii=False) + '\n'
                        )
                        generation_f.flush()
                        if not self.generate_only:
                            generations_to_verify.append(generation_result)
                            if len(generations_to_verify) == self.config["verification"]["batch_size"]:
                                verify_generations()
                finally:
                    logging.warning(f'Generation Task: {i + 1} / {len(generation_futures)} completed!')
            # Handle remain tasks
            if generations_to_verify:
                verify_generations()
            
        logging.warning(f'Total Verification Tasks: {len(verification_futures)}')
        # Get verification results			
        for i, verification_future in enumerate(concurrent.futures.as_completed(verification_futures)):
                try:
                    verification_results = verification_future.result(timeout=self.config["verification"]["timeout"])
                except concurrent.futures.TimeoutError as err:
                    logging.error(f'Timeout in verification!')
                except Exception as err:
                    logging.error(f'Error in verification: {err}')
                    logging.error(f'{traceback.format_exc()}')
                else:
                    data_batch = verification_futures[verification_future]
                    for result, data in zip(verification_results, data_batch):
                        verification_f.write(json.dumps(
                            data | result,
                            ensure_ascii=False) + '\n'
                        )
                        verification_f.flush()
                finally:
                    logging.warning(f'Verification Task: {i + 1} / {len(verification_futures)} completed!')
        
        # Release resources
        if generation_executor:   generation_executor.shutdown()
        if verification_executor: verification_executor.shutdown()

    def verify(self, data_list: list[str]) -> list[str]:
        return [
            self.verifierClient.query(
                query_type = VerifierClient.QueryType.EQUAL,
                data       = {
                   "signal_list" : data["signal_list"],
                   "asrt"        : data["sva"],
                   "ref_asrt"    : data["ground_truth"],
                   "tb"          : data["testbench"],
                   "key_signal"  : "clk",
                }
            )
            for data in data_list
        ]
    
    def generate(self, problem_data: list[dict[str, str]]) -> tuple[list[str]]:
        responses = self.get_responses(problem_data)
        return responses

    def get_responses(self, problem_data: list[dict[str, str]]) -> list[str]:
        config = self.config["generation"]["sva"]
        prompts = [
            Prompter.get_nl2sva_machine_prompt(
                problem    = data["problem"],
                testbench  = data["testbench"]
            )
            for data in problem_data
        ]
        # Query LLM
        responses = self.LLMClient.query(
            prompts           = prompts,
            n                 = 1,
            **config["query"]
        )
        responses = [
            {
                "raw_response": response,
                "sva": Utils.post_process_systemverilog(response),
            }
            for response in responses
        ]
        return responses
