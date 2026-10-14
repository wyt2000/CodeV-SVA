import argparse
import SVAClient.Prompter as Prompter
import SVAClient.Utils as Utils
import re

def get_rl_dataset_for_nl2sva(input_dataset: dict[str, str], double_prompt: bool, use_reasoning: bool):
    output_dataset = []
    for data in input_dataset:
        testbench = Utils.add_sva_to_impl_verify(
            impl           = data["response"],
            asrt           = "// TODO: ASSERTION",
            top_name       = data["top_name"],
            reset          = data["reset"],
            reset_polarity = data["reset_polarity"]
        )
        human_data = {
            "instruction": Prompter.get_nl2sva_human_prompt(
                testbench  = testbench,
                problem = data["specification"] if not data.get("signals", None) 
                               else Utils.add_signal_list_for_spec(data["specification"], data["signals"]),
                example_type = Utils.get_example_type_for_nl2sva(data)
            ),
			"sva": data["sva"].strip(),
            "testbench" : testbench,
            "name": data["name"],
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
                        "data_split": "train",
                        "sva": data["sva"],
                        "testbench": data["testbench"],
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

