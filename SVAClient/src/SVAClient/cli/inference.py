import argparse
import logging
import sys
import yaml
import json

from SVAClient.Prompter import get_formal_proof_prompt
from SVAClient.Utils import post_process_formal_proof

from SVAClient.Client import LLMClient 

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, help="config path")
    args = parser.parse_args()
    
    with open(args.config) as f:
        config = yaml.safe_load(f)

    client = LLMClient(
        host       = config["llm_kit"]["host"],
        port       = config["llm_kit"]["router_port"],
        api_key    = config["llm_kit"]["api_key"],
    )
    client.wait_until_connected()

    dataset = {}
    with open(f"{config['dataset']}") as f:
        for data in f.readlines():
            data = json.loads(data)
            dataset[data['name']] = data

    data = dataset["mathd_algebra_459"]

    formal_statement = '''theorem mathd_algebra_459 (a b c d : ℚ) (h₀ : 3 * a = b + c + d) (h₁ : 4 * b = a + c + d)
    (h₂ : 2 * c = a + b + d) (h₃ : 8 * a + 10 * b + 6 * c = 24) (h₄ : d = 13 / 15) : ↑d.den + d.num = 28 := by
'''

    prompt = get_formal_proof_prompt(
        informal_prefix  = "",
        formal_statement = formal_statement,
        informal_proof   = ""
    )

    prompts = [
        prompt
    ]

    for prompt in prompts:
        responses = client.query(
            prompts           = prompt,
            model             = config["model"],
            n                 = 8,
            max_tokens        = 4096,
            temperature       = 1.0,
            use_chat          = False,
            use_system_prompt = False,
            post_process      = post_process_formal_proof
        )
        print("PROMPT:\n")
        print(prompt)
        for i, r in enumerate(responses):
            print(f"RESPONSE {i}:\n")
            print(r)
