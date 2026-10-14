import argparse
import SVAClient.Prompter as Prompter
import SVAClient.Utils as Utils
import re

def get_rl_dataset_for_nl2sva(input_dataset: dict[str, str], double_prompt: bool, use_reasoning: bool):
    output_dataset = []
    for data in input_dataset:
        human_data = {
            "instruction": Prompter.get_nl2sva_human_prompt(
                testbench = data["testbench"],
                problem = data["problem"]
            ),
			"sva": data["ground_truth"].strip(),
            "testbench" : data["testbench"],
            "name": data["name"],
            "signal_list": Utils.extract_signals_nl2sva_human(
                data["problem"],
                data["testbench"],
                data.get("signals_for_validity", None)
            ),
        }
        output_dataset.append(human_data)

        if not double_prompt: continue
        machine_data = {
            "instruction": Prompter.get_nl2sva_machine_prompt(
                problem = data["specification"]
            ),
			"response": "```systemverilog\n" + re.sub(r"\s*disable\s+iff\s*\([^)]*\)", "", data["sva"].strip())  + "\n```"
		}
        
        output_dataset.append(machine_data)
    return output_dataset

def convert_dataset_to_verl_format(dataset: dict[str, str]):
	formatted_dataset = []
	for data in dataset:
		formatted_dataset.append(
			{
                "name": data["name"],
                "data_source": "sva",
				"prompt": [
					{"role": "system", "content": "You are an AI assistant tasked with formal verification of register transfer level (RTL) designs.\nYour job is to translate a description of an assertion to concrete SystemVerilog Assertion (SVA) implementation.\n"},
					{"role": "user", "content": data["instruction"]},
				],
                "ability": "sva",
                "reward_model": {
                    "style": "rule",
                    "ground_truth": {
                        "data_split": "val",
                        "sva": data["sva"],
                        "testbench": data["testbench"],
                        "signal_list": data["signal_list"]
                    }
                },
        	}
		)
	return formatted_dataset

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-path", type=str, help="The path of the original dataset", required=True)
    parser.add_argument("--output-path", type=str, help="The path of SFT dataset", required=True)
    parser.add_argument("--dataset-format", type=str, help="(verl,)", default="verl")
    parser.add_argument("--double-prompt", help="Use both human and machine prompt", action="store_true")
    parser.add_argument("--use-reasoning", help="Use `raw_response` as the response", action="store_true")
    args = parser.parse_args()

    dataset = Utils.load_dataset(args.input_path)
    dataset = get_rl_dataset_for_nl2sva(dataset, args.double_prompt, args.use_reasoning)
    if args.dataset_format == "verl":
        dataset = convert_dataset_to_verl_format(dataset)
    else:
        assert False, "Invalid dataset format."
    Utils.save_dataset(dataset, args.output_path)

