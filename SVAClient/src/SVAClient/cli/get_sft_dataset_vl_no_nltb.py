import argparse
import SVAClient.Prompter as Prompter
import SVAClient.Utils as Utils
import re

def get_sft_dataset_for_nl2sva(input_dataset: dict[str, str], double_prompt: bool, use_reasoning: bool):
    output_dataset = []
    for data in input_dataset:
        human_data = {
            "name": data["name"],
            "instruction": Prompter.get_wave2sva_prompt(
                signals = Utils.format_list([f"'{signal}'" for signal in data["signals"]])
            ),
			"response": "```systemverilog\n" + data["sva"].strip()  + "\n```"
		}
        output_dataset.append(human_data)
    return output_dataset

def convert_dataset_to_llamafactory_format(dataset: dict[str, str], image_path: str):
	formatted_dataset = []
	for data in dataset:
		if "reasoning" in data:
			response = f"<think>{data['reasoning']}</think>\n{data['response']}"
		else:
			response = data["response"]
		formatted_dataset.append(
			{
				"messages": [
					{"role": "user", "content": data["instruction"] + "<image>"},
					{"role": "assistant", "content": response}
				],
                "images": [
                    f"{image_path}/{data['name']}.png",
                ]
        	}
		)
	return formatted_dataset

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-path", type=str, help="The path of the original dataset", required=True)
    parser.add_argument("--image-path", type=str, help="The path of images of original dataset", required=True)
    parser.add_argument("--output-path", type=str, help="The path of SFT dataset", required=True)
    parser.add_argument("--dataset-format", type=str, help="(llamafactory,)", default="llamafactory")
    parser.add_argument("--double-prompt", help="Use both human and machine prompt", action="store_true")
    parser.add_argument("--use-reasoning", help="Use `raw_response` as the response", action="store_true")
    args = parser.parse_args()

    dataset = Utils.load_dataset(args.input_path)
    dataset = get_sft_dataset_for_nl2sva(dataset, args.double_prompt, args.use_reasoning)
    if args.dataset_format == "llamafactory":
        dataset = convert_dataset_to_llamafactory_format(dataset, args.image_path)
    else:
        assert False, "Invalid dataset format."
    Utils.save_dataset(dataset, args.output_path)

