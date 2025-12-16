import time
import random
import re
import json
import SVAClient.Prompter as Prompter
from copy import deepcopy

START_BACKOFF = 3
MAX_BACKOFF   = 3

def backoff_update(curr_backoff):
	time.sleep(curr_backoff)
	curr_backoff *= 1.5
	curr_backoff = min(curr_backoff, MAX_BACKOFF)
	curr_backoff += random.random() * curr_backoff / 3
	return curr_backoff

def extract_after_last_think(text):
    tag = "</think>"
    idx = text.rfind(tag)
    if idx != -1:
        return text[idx + len(tag):].strip()
    else:
        return text

def post_process_systemverilog(response):
    response = extract_after_last_think(response)
    if "```systemverilog" in response:
        response = response.split("```systemverilog")[-1]
    if "```" in response:
        response = response.split("```")[0]
    return response.strip()

def extract_signals_nl2sva_human(problem, testbench, signal_list=None):
    prompt = Prompter.get_nl2sva_human_prompt(
        problem   = problem,
        testbench = testbench
    )
    if signal_list is None:
        signal_list_copy = re.findall(r"'([^'\s]+)'", prompt)
    else:
        signal_list_copy = deepcopy(signal_list)
    params = re.findall(
        r"\b(parameter|localparam)\s+(int\s+|real\s+|bit\s+|\[[^]]+\]\s*)?(\w+)",
        prompt,
    )
    params = [m[2] for m in params]
    signal_list_copy.extend(params)
    signal_list_text = ",".join(signal_list_copy)
    return signal_list_text

def extract_signals_nl2sva_machine(ground_truth):
    signal_list = re.findall(r"\bsig_\w+", ground_truth)
    signal_list = list(set(signal_list))
    signal_list_text = ",".join(signal_list)
    return signal_list_text

PROPERTY_PATTERN = re.compile(r'### Property \d+\n(.+?)(?=\n### Property|\Z)', re.DOTALL)
def post_process_specification(response):
    response = [prop.strip() for prop in PROPERTY_PATTERN.findall(response)]
    return response

def add_sva_to_impl_verify(impl: str, asrt: str, top_name: str, reset: str, reset_polarity: bool | None) -> str:
    """
    1. Add `tb_reset` as the real reset signal.
    2. Insert `asrt` at the end of the module `top_name`.
    """
    pattern = re.compile(
        rf"(module\s+{top_name}\b[\s\S]*?)(endmodule)",
        re.MULTILINE
    )

    def replacer(match):
        module_body = match.group(1)
        endmodule = match.group(2)
        if reset_polarity is not None:
            result = module_body
            result += f"\nwire tb_reset;\n"
            result += f"assign tb_reset = ({reset} == 1'b{1 if reset_polarity else 0});\n"
            result += f"{asrt}\n"
            result += endmodule
            return result
        return f"{module_body}\n    {asrt}\n{endmodule}"

    new_code, count = pattern.subn(replacer, impl, count=1)
    if count == 0:
        raise ValueError(f"Module {top_name} not found in code.")
    return new_code

def load_dataset(path):
    dataset = []
    with open(path) as f:
        for data in f:
            data = json.loads(data)
            dataset.append(data)
    return dataset

def save_dataset(dataset, path):
    with open(path, 'w') as f:
        for data in dataset:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")

def get_example_type_for_nl2sva(data):
    # Dispatch example type
    if data["clk"] is not None and data["reset"] is not None:
        example_type = "seq"
    elif data["clk"] is None and data["reset"] is None:
        example_type = "comb"
    elif data["clk"] is not None and data["reset"] is None:
        example_type = "clk_only"
    elif data["clk"] is None and data["reset"] is not None:
        example_type = "seq"
    else:
        assert False, f"Invalid data: {data}"
    return example_type

def format_list(lst):
    if not lst:
        return ""
    elif len(lst) == 1:
        return str(lst[0])
    elif len(lst) == 2:
        return f"{lst[0]} and {lst[1]}"
    else:
        return ", ".join(map(str, lst[:-1])) + f" and {lst[-1]}"

def add_signal_list_for_spec(spec: str, signal_list: list[str]) -> str:
	return spec + " Use the signals " + format_list([f"'{signal}'" for signal in signal_list]) + "."

def post_process_verilog(response):
    response = extract_after_last_think(response)
    if "```verilog" in response:
        response = response.split("```verilog")[-1]
    if "```" in response:
        response = response.split("```")[0]
    return response.strip()

def insert_disable_iff(text):
    if re.search(r'disable\s+iff\s*\(\s*tb_reset\s*\)', text):
        return text
    pattern = r'\(\s*posedge\s+clk\s*\)'
    replacement = r'(posedge clk) disable iff (tb_reset)'
    return re.sub(pattern, replacement, text, count=1)

def post_process_systemverilog_add_disable_clause(response):
    response = post_process_systemverilog(response)
    response = insert_disable_iff(response)
    return response
