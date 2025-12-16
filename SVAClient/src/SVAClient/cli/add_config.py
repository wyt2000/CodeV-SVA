import yaml
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--template-path",     type=str, help="Original config file",                   required=True)
parser.add_argument("--save-path",         type=str, help="New config file",                        required=True)
parser.add_argument("--problem-path",      type=str, help="The path to load problem",               default=None)
parser.add_argument("--generation-path",   type=str, help="The path to save generation results",    default=None)
parser.add_argument("--verification-path", type=str, help="The path to save verification results",  default=None)
parser.add_argument("--model-path",        type=str, help="The path or name of the autoformalizer", default=None)
parser.add_argument("--tokenizer-path",    type=str, help="The path of tokenizer",                  default=None)
parser.add_argument("--max-tokens",        type=int, help="max tokens for llm",                     default=None)
parser.add_argument("--num-samples",       type=int, help="number of samples",                      default=None)
args = parser.parse_args()

with open(args.template_path) as f:
    config = yaml.safe_load(f)

if args.problem_path is not None:
    config["agent"]["problem"]["path"] = args.problem_path
if args.generation_path is not None:
    config["agent"]["generation"]["path"] = args.generation_path
if args.verification_path is not None:
    config["agent"]["verification"]["path"] = args.verification_path
if args.model_path is not None:
    config["agent"]["problem"]["models"][0]["sva"] = args.model_path
    config["agent"]["generation"]["sva"]["query"]["model"] = args.model_path
    if "models" in config["llm_kit"]:
        config["llm_kit"]["models"][0]["model"] = args.model_path
if args.tokenizer_path is not None:
    config["agent"]["generation"]["sva"]["query"]["tokenizer_path"] = args.tokenizer_path
if args.max_tokens is not None:
    config["agent"]["generation"]["sva"]["query"]["max_tokens"] = args.max_tokens
if args.num_samples is not None:
    config["agent"]["problem"]["num_samples"] = args.num_samples


with open(args.save_path, "w") as f:
    yaml.safe_dump(config, f)

print(f"Config save in {args.save_path}!")
print(config)
