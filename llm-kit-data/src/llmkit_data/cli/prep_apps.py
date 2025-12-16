import argparse
import json

from llmkit_data.utils.json import read_jsonl, write_jsonl
from llmkit_data.std.datasets import CODE_TEMPLATE


def mk_prompt(doc):
    prompt = "Write Python code to solve competitive programming problems in a markdown code block."

    starter_code = None if len(doc["starter_code"]) == 0 else doc["starter_code"]
    try:
        input_outpout = json.loads(doc["input_output"])
        fn_name = None if not input_outpout.get("fn_name") else input_outpout["fn_name"]
    except ValueError:
        fn_name = None
    prompt += "\nQUESTION:\n"
    prompt += doc["question"]
    if starter_code:
        prompt += starter_code
    if not fn_name:
        prompt += "\nUse Standard Input format"
    else:
        prompt += "\nUse Call-Based format"

    prompt += "\nPlease generate the code in a ```python markdown block, ensuring to include the closing ``` at the end."

    conversation = [{"role": "user", "content": prompt}]
    return conversation


def convert_to_sft(path, prompt_only):
    for sample in read_jsonl(path):
        problem_id = sample["id"]

        try:
            json.loads(sample["input_output"])
            solutions = json.loads(sample["solutions"])
        except ValueError:
            print(f"Skipping {problem_id}: Invalid JSON in input_output/solutions")
            continue

        question = mk_prompt(sample)
        if prompt_only:
            yield {"question": question, "problem_id": problem_id}
        else:
            for solution in solutions:
                yield {
                    "question": question,
                    "response": [
                        {"role": "assistant", "content": CODE_TEMPLATE.format(solution)}
                    ],
                    "problem_id": problem_id
                }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--apps", type=str, help="apps dataset path")
    parser.add_argument("--out", type=str, help="output path")
    parser.add_argument("--type", type=str, choices=["SFT", "Reward"])
    parser.add_argument(
        "--prompt_only",
        action="store_true",
        help="generate prompts specifically for evaluation",
    )
    args = parser.parse_args()

    match args.type:
        case "SFT":
            write_jsonl(convert_to_sft(args.apps, args.prompt_only), args.out)
        case "Reward":
            raise NotImplementedError("Reward")
        case other:
            raise NotImplementedError("Unknown dataset")
