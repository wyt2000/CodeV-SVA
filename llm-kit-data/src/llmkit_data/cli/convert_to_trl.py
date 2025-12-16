import argparse

from llmkit_data.utils.json import read_jsonl, write_jsonl
from llmkit_data.std.datasets import detect_dataset_type
from llmkit_data.converter.trl import (
    stdsft_to_trl
)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=str, help="dataset path")
    parser.add_argument("--out", type=str, help="output path")
    args = parser.parse_args()

    dataset = list(read_jsonl(args.dataset))

    match detect_dataset_type(dataset[0]):
        case "SFT":
            new_dataset = stdsft_to_trl(dataset)
        case "Reward":
            raise NotImplementedError("Reward dataset")
        case other:
            raise NotImplementedError("Unknown dataset")

    write_jsonl(new_dataset, args.out)
