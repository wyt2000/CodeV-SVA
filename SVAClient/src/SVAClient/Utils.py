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

def post_process_systemverilog_no_tbreset(response):
    response = post_process_systemverilog(response)
    response = re.sub(r"\s*disable\s+iff\s*\([^)]*\)", "", response.strip())
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

def format_list_chinese(lst):
    if not lst:
        return ""
    elif len(lst) == 1:
        return str(lst[0])
    elif len(lst) == 2:
        return f"{lst[0]} 和 {lst[1]}"
    else:
        return "， ".join(map(str, lst[:-1])) + f" 和 {lst[-1]}"

def add_signal_list_for_spec_chinese(spec: str, signal_list: list[str]) -> str:
	return spec + "请使用以下信号：" + format_list_chinese([f"'{signal}'" for signal in signal_list]) + "。"

def post_process_orm_judgement(response):
    matches = re.findall(r"\**Final Score\**:\**\s*\**(10|[1-9])(?:/10)?\**", response)
    if matches:
        try:
            last_score = int(matches[-1])
            return last_score
        except Exception as err:
            pass
    return 0

def post_process_verilog(response):
    response = extract_after_last_think(response)
    if "```verilog" in response:
        response = response.split("```verilog")[-1]
    if "```" in response:
        response = response.split("```")[0]
    return response.strip()

def remove_verilog_assertions(code):
    """
    清除Verilog代码中的所有assertion和SVA
    """
    
    # 模式1：删除完整的SVA property块
    # 匹配 property ... endproperty 块（支持多行）
    property_pattern = r'\bproperty\s+\w+\s*;.*?endproperty\s*;?\s*'
    # 使用 re.DOTALL 使 . 匹配换行符
    code = re.sub(property_pattern, '', code, flags=re.DOTALL | re.IGNORECASE)
    
    # 模式2：删除 assert property 语句
    # 匹配: assert property(...); 以及带标签的断言
    assert_property_pattern = r'\w*\s*:\s*assert\s+property\s*\([^;]+\)\s*;'
    code = re.sub(assert_property_pattern, '', code, flags=re.IGNORECASE)
    
    # 模式3：删除 always块中的简单assert语句（带$fatal或其他任务的）
    # 匹配: assert (condition) else $fatal(...);
    simple_assert_pattern = r'\s*assert\s*\([^;]+\)\s*else\s*\$[a-z_]+\([^;]+\)\s*;'
    code = re.sub(simple_assert_pattern, '', code, flags=re.IGNORECASE)
    
    # 模式4：删除独立的assert语句
    # 匹配: assert (condition);
    standalone_assert_pattern = r'\s*assert\s*\([^;]+\)\s*;'
    code = re.sub(standalone_assert_pattern, '', code)
    
    # 模式5：删除 cover property 语句（如果需要）
    cover_property_pattern = r'\w*\s*:\s*cover\s+property\s*\([^;]+\)\s*;'
    code = re.sub(cover_property_pattern, '', code, flags=re.IGNORECASE)
    
    # 模式6：删除 assume property 语句
    assume_property_pattern = r'\w*\s*:\s*assume\s+property\s*\([^;]+\)\s*;'
    code = re.sub(assume_property_pattern, '', code, flags=re.IGNORECASE)
    
    # 移除因删除assertion而产生的多余空行
    code = re.sub(r'\n\s*\n\s*\n', '\n\n', code)
    
    return code

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

def post_process_wavedrom(response):
    response = extract_after_last_think(response)
    if "```wavedrom" in response:
        response = response.split("```wavedrom")[-1]
    if "```" in response:
        response = response.split("```")[0]
    return response.strip()

def post_process_svg(response):
    response = extract_after_last_think(response)
    if "```svg" in response:
        response = response.split("```svg")[-1]
    if "```" in response:
        response = response.split("```")[0]
    return response.strip()

def post_process_signal_analysis(response: str) -> str:
    """Post-process stage 1 response: extract JSON signal analysis.

    1. Extract text after the last </think> tag (if present).
    2. Try to extract and parse a JSON block from that text.
    3. If JSON parse fails, return the text after </think> as fallback.
    """
    response = extract_after_last_think(response)

    # Try  code block
    if '```json' in response:
        try:
            json_str = response.split('```json')[1].split('```')[0].strip()
            json.loads(json_str)
            return json_str
        except (IndexError, json.JSONDecodeError):
            pass

    # Try generic  code block
    if '```' in response:
        try:
            json_str = response.split('```')[1].split('```')[0].strip()
            json.loads(json_str)
            return json_str
        except (IndexError, json.JSONDecodeError):
            pass

    # Try to find a JSON object by matching braces
    brace_depth = 0
    start_idx = None
    for i, ch in enumerate(response):
        if ch == '{':
            if brace_depth == 0:
                start_idx = i
            brace_depth += 1
        elif ch == '}':
            brace_depth -= 1
            if brace_depth == 0 and start_idx is not None:
                candidate = response[start_idx:i+1]
                try:
                    json.loads(candidate)
                    return candidate
                except json.JSONDecodeError:
                    start_idx = None

    # Fallback: return the text after </think> as-is
    return response.strip()
