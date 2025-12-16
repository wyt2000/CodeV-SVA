from openai import OpenAI
from anthropic import Anthropic
import requests
import time
import logging
import os
from typing import List, Callable, Any
from abc import ABC, abstractmethod
from transformers import AutoTokenizer
import traceback
from enum import Enum

from SVAClient.Utils import START_BACKOFF, backoff_update

CONNECTION_INTERVAL = 3

class Client(ABC):

    def wait_until_connected(self, time_interval=CONNECTION_INTERVAL):
        while True:
            try:
                requests.get(self.url)
                return
            except requests.exceptions.RequestException as e:
                logging.warning(f"{self.__class__.__name__}: Waiting for server at {self.url}...")
            time.sleep(time_interval)

    def query(self, **kwargs) -> Any:
        curr_backoff = START_BACKOFF
        while True:
            try:
                return self._query_impl(**kwargs)
            except Exception as err:
                logging.error(f"Error in {self.__class__.__name__}: {err}, waiting {curr_backoff} seconds and then retrying...")
                logging.error(traceback.format_exc())
                curr_backoff = backoff_update(curr_backoff)
                continue

class VerifierClient(Client):
    VERIFIER_SERVER_HEADER  = {"Content-Type": "application/json"}

    class QueryType(Enum):
        SYNTAX             = 1
        VERIFY             = 2
        EQUAL              = 3
        COV                = 4
        TESTBENCH          = 5
        VERIFY_IMPL_ONLY   = 6
        MVOTE              = 7
        EQUAL_OPT          = 8

    def __init__(self, host: str, port: int):
        self._url = f"http://{host}:{port}"

    @property
    def url(self) -> str:
        return self._url

    def get_query_type(self, query_type: QueryType):
        if query_type == self.QueryType.SYNTAX:
            return "syntax"
        if query_type == self.QueryType.VERIFY:
            return "verify"
        if query_type == self.QueryType.EQUAL:
            return "equal"
        if query_type == self.QueryType.COV:
            return "conv"
        if query_type == self.QueryType.TESTBENCH:
            return "testbench"
        if query_type == self.QueryType.VERIFY_IMPL_ONLY:
            return "verify_impl_only"
        if query_type == self.QueryType.MVOTE:
            return "mvote"
        if query_type == self.QueryType.EQUAL_OPT:
            return "equal_opt"
        assert False, f"Unknown query type: {query_type}"

    def _query_impl(self, query_type: str, data: dict[str, str]) -> dict[str, str]:
        response = requests.post(url=f"{self.url}/{self.get_query_type(query_type)}", json=data, headers=self.VERIFIER_SERVER_HEADER)
        if response.status_code == 200:
            responses = response.json()
            return responses
        raise Exception(f"Response Code: {response.status_code}, {response.text}")
        
class LLMClient(Client):
    def __init__(self, config: dict[str, str]):
        self.server_type = config.get("server_type", "openai")

        if self.server_type == "vllm":
            self._url = f"http://{config['host']}:{config['router_port']}/v1"
            self.api_key  = config["api_key"]
            self._client  = OpenAI(
                base_url  = self.url,
                api_key   = self.api_key,
            )
            self._tokenizers = {}
            self._query_impl = self._query_impl_vllm

        elif self.server_type == "openai_api":
            self._url = config['url']
            self._client = OpenAI(
                api_key  = os.environ.get("OPENAI_API_KEY"),
                base_url = self.url
            )
            self._query_impl = self._query_impl_openai

        elif self.server_type == "azure_api":
            self._url = config['url']
            self._client = OpenAI(
                api_key  = os.environ.get("AZURE_API_KEY"),
                base_url = self.url
            )
            self._query_impl = self._query_impl_openai

        elif self.server_type == "ark_api":
            self._url = config['url']
            self._client = OpenAI(
                api_key  = os.environ.get("ARK_API_KEY"),
                base_url = self.url
            )
            self._query_impl = self._query_impl_openai



        elif self.server_type == "anthropic":
            self._url = config['url']
            self._client = Anthropic(
                api_key  = os.environ.get("API_KEY"),
                base_url = self.url
            )
            self._query_impl = self._query_impl_anthropic

        else:
            raise ValueError(f"Unsupport server_type: {self.server_type}")

    @property
    def url(self) -> str:
        return self._url

    def _query_impl_vllm(self, prompts: str | List[str], response_prefixes: str | List[str] | None = None, system_prompt: str = "", use_system_prompt: bool = True, use_chat: bool = True, post_process: Callable[[str], str] = lambda _ : _, tokenizer_path: str | None = None, **kwargs) -> List[str]:
        # Prepare response prefixes
        if isinstance(prompts, str):
            prompts = [prompts]
        if response_prefixes is None:
            response_prefixes = [''] * len(prompts)
        if isinstance(response_prefixes, str):
            response_prefixes = [response_prefixes] * len(prompts)
        assert len(response_prefixes) == len(prompts)

        if "enable_thinking" in kwargs:
            enable_thinking = kwargs["enable_thinking"]
            del kwargs["enable_thinking"]
        else:
            enable_thinking = True 

        # Add special tokens 
        if use_chat:
            tokenizer = self._tokenizers.get(
                tokenizer_path,
                AutoTokenizer.from_pretrained(tokenizer_path, trust_remote_code=True)
            )
            if use_system_prompt:
                prompts = [
                    tokenizer.apply_chat_template(
                        [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt}
                        ],
                        tokenize=False,
                        add_generation_prompt=True,
                        enable_thinking=enable_thinking
                    )
                    for prompt in prompts
                ]
            else:
                prompts = [
                    tokenizer.apply_chat_template(
                        [
                            {"role": "user", "content": prompt}
                        ],
                        tokenize=False,
                        add_generation_prompt=True,
                        enable_thinking=enable_thinking
                    )
                    for prompt in prompts
                ]

        # Add response prefixes
        prompts = [prompt + response_prefix for prompt, response_prefix in zip(prompts, response_prefixes)]

        # Query LLM
        completions = self._client.completions.create(
            prompt  = prompts,
            extra_headers = {
                "model" : kwargs["model"]
            },
            extra_body = {
                "repetition_penalty" : 1.0,
                "chat_template_kwargs": {"enable_thinking": enable_thinking}
            },
            **kwargs
        )
        try:
            logging.info(f"Response Prefixes: {response_prefixes}")
            logging.info(f"System Prompt: {system_prompt}")
            logging.info(f"Prompt: {prompts if isinstance(prompts, str) else prompts[0]}")
            logging.info(f"Query result: {completions.choices[0].text}")
            results = [post_process(completion.text) for completion in completions.choices]
            results = [response_prefix + result for response_prefix, result in zip(response_prefixes, results)]
            logging.info(f"Query result after postprocess: {results[0]}")
            return results
        except Exception as err:
            logging.error(err)
            logging.error(traceback.format_exc())
            logging.error(f'prompt = {prompts}')
            logging.error(f'completions = {completions}')
            return []

    def _query_impl_openai(self, prompts: str | List[str], response_prefixes: str | List[str] | None = None, system_prompt: str = "", use_system_prompt: bool = True, use_chat: bool = True, post_process: Callable[[str], str] = lambda _ : _, tokenizer_path: str | None = None, **kwargs) -> List[str]:
        assert tokenizer_path is None, "Invalid argument in openai api: tokenizer_path."
        assert use_chat == True
        # Prepare response prefixes
        if isinstance(prompts, str):
            prompts = [prompts]
        if response_prefixes is None:
            response_prefixes = [''] * len(prompts)
        if isinstance(response_prefixes, str):
            response_prefixes = [response_prefixes] * len(prompts)
        assert len(response_prefixes) == len(prompts)
        response_prefixes = [response_prefix.strip('\n').strip() for response_prefix in response_prefixes]

        # Query LLM
        all_results = []
        for prompt, response_prefix in zip(prompts, response_prefixes):
            completions = self._client.chat.completions.create(
                messages =
                    ([{"role": "system", "content": system_prompt}] if use_system_prompt else [])
                    +
                    [{"role": "user", "content": prompt}] 
                    + 
                    ([{"role": "assistant", "content": response_prefix}] if response_prefix else [])
                ,
                **kwargs
            )
            try:
                logging.info(f"System Prompt: {system_prompt}")
                logging.info(f"Prompt: {prompt}")
                logging.info(f"Query result: {completions.choices[0].message.content}")
                results = [
                    post_process(
                        (("<think>" + completion.message.reasoning_content + "</think>") if (hasattr(completion.message, "reasoning_content") and completion.message.reasoning_content) else "") +
                        completion.message.content
                    ) 
                    for completion in completions.choices
                ]
                results = [response_prefix + result for response_prefix, result in zip(response_prefixes, results)]
                logging.info(f"Query result after postprocess: {results[0]}")
            except Exception as err:
                logging.error(err)
                logging.error(traceback.format_exc())
                logging.error(f'prompt = {prompt}')
                logging.error(f'completions = {completions}')
                results = []
            all_results.extend(results)
        return all_results


    def _query_impl_anthropic(self, prompts: str | List[str], response_prefixes: str | List[str] | None = None, system_prompt: str = "", use_system_prompt: bool = True, use_chat: bool = True, post_process: Callable[[str], str] = lambda _ : _, tokenizer_path: str | None = None, **kwargs) -> List[str]:
        assert tokenizer_path is None, "Invalid argument in anthropic api: tokenizer_path."
        assert use_chat == True
        assert kwargs["n"] == 1
        del kwargs["n"]
        if "stop" in kwargs:
            kwargs["stop_sequences"] = kwargs["stop"]
            del kwargs["stop"]
        # Prepare response prefixes
        if isinstance(prompts, str):
            prompts = [prompts]
        if response_prefixes is None:
            response_prefixes = [''] * len(prompts)
        if isinstance(response_prefixes, str):
            response_prefixes = [response_prefixes] * len(prompts)
        assert len(response_prefixes) == len(prompts)
        response_prefixes = [response_prefix.strip('\n').strip() for response_prefix in response_prefixes]
        if use_system_prompt:
            kwargs["system"] = system_prompt

        # Query LLM
        all_results = []
        for prompt, response_prefix in zip(prompts, response_prefixes):
            completions = self._client.messages.create(
                messages = [{"role": "user", "content": prompt}] + ([{"role": "assistant", "content": response_prefix}] if response_prefix else []),
                extra_headers = {
                    "Authorization" : f"Bearer {self._client.api_key}"
                },
                **kwargs
            )
            try:
                logging.info(f"System Prompt: {kwargs['system']}")
                logging.info(f"Prompt: {prompt}")
                logging.info(f"Query result: {completions.content[0].text}")
                results = [post_process(completion.text) for completion in completions.content]
                results = [response_prefix + "\n" + result for response_prefix, result in zip(response_prefixes, results)]
                logging.info(f"Query result after postprocess: {results[0]}")
            except Exception as err:
                logging.error(err)
                logging.error(traceback.format_exc())
                logging.error(f'prompt = {prompt}')
                logging.error(f'completions = {completions}')
                results = []
            all_results.extend(results)
        return all_results
