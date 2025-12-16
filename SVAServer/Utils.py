import os
import re
from typing import List, Set, Tuple
import subprocess
import json
import networkx as nx
import time

config_global = None

def extract_signal_names(module_interface: str) -> Set[str]:
    """
    Extract signal names from the module interface.

    Args:
        module_interface (str): The module interface declaration.

    Returns:
        Set[str]: A set of signal names found in the interface.
    """
    # Regular expression to match signal declarations
    signal_pattern = (
        r'\b(?:input|output|inout)\s+(?:reg|wire)?\s*(?:\[[^\]]+\])?\s*(\w+)'
    )

    # Find all matches
    matches = re.findall(signal_pattern, module_interface)

    # Extract signal names from matches
    signal_names = set(matches)

    return signal_names

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

def add_sva_to_tb_verify(tb: str, asrt: str) -> str:
    prefix, suffix = tb.rsplit("endmodule", 1)
    packaged_tb_text = (
        prefix
        + "\n\n"
        + asrt
        + "\n\n"
        + "endmodule"
        + suffix
    )
    return packaged_tb_text

def add_sva_to_tb_equal(tb: str, asrt: str, ref_asrt: str) -> str:
    prefix, suffix = tb.rsplit("endmodule", 1)
    packaged_tb_text = (
        prefix
        + "\n\n"
        + ref_asrt.replace("asrt", "reference")
        + "\n\n"
        + asrt
        + "\n\n"
        + "endmodule"
        + suffix
    )
    return packaged_tb_text

def sv_sva_to_tb(sv_code: str, sva_codes: str | List[str]) -> str:
    # Use regex to find the module declaration and interface
    module_match = re.search(
        r'module\s+(\w+)\s*\((.*?)\);', sv_code, re.DOTALL
    )
    if not module_match:
        raise ValueError("Could not find module declaration in the original SV code.")

    module_name = module_match.group(1)
    interface = module_match.group(2)

    # Remove type declarations and replace output/inout with input
    # Match each port line
    port_lines = re.findall(r'([^\n,]+)', interface)
    tb_ports = []
    for line in port_lines:
        # Remove comments and extra spaces
        line = line.split('//')[0].strip()
        if not line:
            continue
        # Replace output/inout with input
        line = re.sub(r'\b(output|inout)\b', 'input', line)
        # Remove type keywords (logic, reg, wire)
        line = re.sub(r'\blogic\b|\breg\b|\bwire\b', '', line)
        # Remove extra spaces
        line = re.sub(r'\s+', ' ', line).strip()
        tb_ports.append(line)

    tb_interface = ',\n'.join(tb_ports)
    tb_module = f"module {module_name}_tb (\n{tb_interface}\n);"

    if isinstance(sva_codes, str):
        sva_codes = [sva_codes]

    for i, sva_code in enumerate(sva_codes):
        if not sva_code.strip():
            continue
        property_name = f"a{i}"
        tb_module += f"\nproperty {property_name};\n"
        tb_module += f"{sva_code}\n"
        tb_module += f"endproperty\n"
        tb_module += (
            f"assert_{property_name}: assert property({property_name});\n"
        )

    tb_module += "\nendmodule\n"

    return tb_module

def auto_top(verilog_code):
    """
    自动找到verilog代码中的顶层模块，当前实现为找到最大的调用子树的根节点，当两个调用字数大小相同时，选择字典序最小的

    输入：
    verilog_code: verilog代码字符串
    输出：
    top_module: 顶层模块名
    """
    instance_graph = nx.DiGraph()
    note_pattern = r"(//[^\n]*|/\*[\s\S]*?\*/)"
    new_code = re.sub(note_pattern, "", verilog_code)
    new_code = re.sub(r"(?:\s*?\n)+", "\n", new_code)
    module_def_pattern = r"(module\s+)([a-zA-Z_][a-zA-Z0-9_\$]*|\\[!-~]+?(?=\s))(\s*\#\s*\([\s\S]*?\))?(\s*(?:\([^;]*\))?\s*;)([\s\S]*?)?(endmodule)"
    module_defs = re.findall(module_def_pattern, new_code, re.DOTALL)
    if not module_defs:
        raise Exception("No module found in auto_top().")
    module_names = [m[1] for m in module_defs]
    instance_graph.add_nodes_from(module_names)
    # 匹配 module 到 endmodule 之间的内容，并提取模块名
    for mod in module_defs:
        this_mod_name = mod[1]
        this_mod_body = mod[4]
        for submod in module_names:
            if submod != this_mod_name:
                module_instance_pattern = rf"({re.escape(submod)})(\s)(\s*\#\s*\([\s\S]*?\))?([a-zA-Z_][a-zA-Z0-9_\$]*|\\[!-~]+?(?=\s))(\s*(?:\([^;]*\))?\s*;)"
                module_instances = re.findall(
                    module_instance_pattern, this_mod_body, re.DOTALL
                )
                if module_instances:
                    instance_graph.add_edge(this_mod_name, submod)
    instance_tree_size = {}
    for n in instance_graph.nodes:
        if instance_graph.in_degree(n) == 0:
            instance_tree_size[n] = nx.descendants(instance_graph, n)
    top_module = max(instance_tree_size, key=instance_tree_size.get)
    return top_module

def extract_golden_ports(golden_path, golden_top, timeout=60):
    """
    根据yosys的结果，提取golden模块的输入输出端口、时钟端口、复位端口。
    golden_path: 参考设计的路径
    golden_top: 参考设计的顶层模块名

    输出：
    为一个元组(input_port_width, output_port_width, clock_port_polarity, reset_port_polarity_sync)
    input_port_width: 输入端口名、位宽
    output_port_width: 输出端口名、位宽
    clock_port_polarity: 时钟端口名、上升沿/下降沿触发
    reset_port_polarity_sync: 复位端口名、高低电平有效、同步/异步复位
    """
    golden_top = golden_top.lstrip("\\")
    yosys_script = f"read_verilog {golden_path}; prep -top {golden_top} -flatten; opt_dff -nodffe; json -compat-int; exec -- echo 'Happy new year~';"
    yosys_result = subprocess.run(
        ["yosys", "-p", yosys_script],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
    )
    if yosys_result.stderr:
        raise Exception(yosys_result.stderr.decode("utf-8"))
    yosys_output = yosys_result.stdout.decode("utf-8")
    yosys_json_text = re.search(
        r'(\{\n\s+"creator":[\s\S]*\})\n+[\d]+\. Executing command',
        yosys_output,
        re.DOTALL,
    ).group(1)
    yosys_json = json.loads(yosys_json_text)
    ports_ids_dict = {}
    input_port_width = set()
    output_port_width = set()
    if yosys_json["modules"] == {}:
        raise Exception("No module found in yosys output after synthesis.")
    for port_name in yosys_json["modules"][golden_top]["ports"]:
        direction = yosys_json["modules"][golden_top]["ports"][port_name][
            "direction"
        ]
        bits = yosys_json["modules"][golden_top]["ports"][port_name]["bits"]
        width = len(bits)
        ports_ids_dict[port_name] = bits
        if direction == "input":
            input_port_width.add((port_name, width))
        if direction == "output":
            output_port_width.add((port_name, width))
    clock_port_polarity = set()
    reset_port_polarity_sync = set()

    def find_single_port(port_id, ports_ids_dict):
        if len(port_id) != 1:
            raise Exception("Only support single port id now.")
        for port_name, bits in ports_ids_dict.items():
            if len(bits) == 1 and bits[0] == port_id[0]:
                return port_name
            elif len(bits) > 1 and port_id[0] in bits:
                return f"{port_name}[{bits.index(port_id[0])}]"
        else:
            return None

    for cell_id in yosys_json["modules"][golden_top]["cells"]:
        cell = yosys_json["modules"][golden_top]["cells"][cell_id]
        for reg_ports in cell["connections"]:
            if reg_ports == "CLK":
                port_id = cell["connections"][reg_ports]
                port_name = find_single_port(port_id, ports_ids_dict)
                if port_name:
                    polarity = cell["parameters"]["CLK_POLARITY"]
                    clock_port_polarity.add((port_name, polarity))
                break
        match cell["type"]:
            case "$adff" | "$adffe" | "$adlatch":
                for reg_ports in cell["connections"]:
                    if reg_ports == "ARST":
                        port_id = cell["connections"][reg_ports]
                        port_name = find_single_port(port_id, ports_ids_dict)
                        if port_name:
                            polarity = cell["parameters"]["ARST_POLARITY"]
                            sync = False
                            reset_port_polarity_sync.add(
                                (port_name, polarity, sync)
                            )
                        break
            case "$sdff" | "$sdffe" | "$sdffce":
                for reg_ports in cell["connections"]:
                    if reg_ports == "SRST":
                        port_id = cell["connections"][reg_ports]
                        port_name = find_single_port(port_id, ports_ids_dict)
                        if port_name:
                            polarity = cell["parameters"]["SRST_POLARITY"]
                            sync = True
                            reset_port_polarity_sync.add(
                                (port_name, polarity, sync)
                            )
                        break
            case "$dffsr" | "$dffsre" | "$dlatchsr" | "$sr":
                for reg_ports in cell["connections"]:
                    if reg_ports == "SET" or reg_ports == "CLR":
                        port_id = cell["connections"][reg_ports]
                        port_name = find_single_port(port_id, ports_ids_dict)
                        if port_name:
                            polarity = cell["parameters"][f"{reg_ports}_POLARITY"]
                            sync = False
                            reset_port_polarity_sync.add(
                                (port_name, polarity, sync)
                            )
                        break
            case "$dlatch" | "$ff" | "$dff" | "$dffe" | "aldff" | "$aldffe":
                pass
            case _:
                pass
    return (
        input_port_width,
        output_port_width,
        clock_port_polarity,
        reset_port_polarity_sync,
    )

def get_tb_code(
    top_name,
    input_port_width,
    output_port_width,
    clock_port_polarity,
    reset_port_polarity_sync,
):
    """
    根据输入输出端口、时钟端口、复位端口，生成testbench代码。

    输入：
    top_name: 主模块名
    input_port_width: 输入端口名、位宽，为一个集合，其中的元素为(port_name, width)
    output_port_width: 输出端口名、位宽，为一个集合，其中的元素为(port_name, width)
    clock_port_polarity:
        时钟端口名、上升沿/下降沿触发
        为一个集合，其中的元素为(port_name, polarity)
        port_name是端口名，字符串
        polarity是时钟信号的极性，1表示上升沿触发，0表示下降沿触发
    reset_port_polarity_sync:
        复位信号的端口名、高低电平有效、同步/异步复位
        为一个集合，其中的元素为(port_name, polarity, sync)
        port_name是端口名，字符串
        polarity是复位信号的极性，1表示高电平有效，0表示低电平有效
        sync是复位信号的同步异步，True表示同步复位，False表示异步复位

    输出：testbench代码
    """
    if len(clock_port_polarity) > 1:
        raise Exception(
            "Multiple clock ports or multiple triggering edge detected, currently not supported."
        )

    if len(reset_port_polarity_sync) > 1:
        raise Exception(
            "Multiple reset prots detected, currently not supported."
        )

    # 生成输入信号定义
    input_defs = ",\n".join(
        [
            f"    input wire [{width-1}:0] {port}" if width > 1 else f"    input wire {port}"
            for port, width in sorted(list(input_port_width) + list(output_port_width))
        ]
    )

    # 生成完整的 testbench 代码
    tb_module = f"module {top_name}_tb (\n{input_defs}\n);"
    if len(reset_port_polarity_sync) == 1:
        rst_name, rst_polarity, rst_sync = list(reset_port_polarity_sync)[0]
        tb_module += f"\n\n    wire tb_reset;\n"
        tb_module += f"    assign tb_reset = ({rst_name} == 1'b{1 if rst_polarity else 0});\n"
    tb_module += "\nendmodule\n"
    tb_module += f"\nbind {top_name} {top_name}_tb {top_name}_tb_inst (.*);\n"
    return tb_module

def get_clk_and_rst_name(
    clock_port_polarity,
    reset_port_polarity_sync,
):
    clk, rst, rst_polarity = None, None, None
    if len(clock_port_polarity) == 1:
        clk = list(clock_port_polarity)[0][0]
    if len(reset_port_polarity_sync) == 1:
        rst = list(reset_port_polarity_sync)[0][0]
        rst_polarity = (list(reset_port_polarity_sync)[0][1] == 1)
    return clk, rst, rst_polarity

def calculate_jg_metric_for_verify(jasper_out_str: str):
    # check for syntax error
    syntax_error_match = re.findall(r"syntax error", jasper_out_str)
    if syntax_error_match:
        return {
            "syntax": 0.0,
            "functionality": 0.0,
            "func_relaxed": 0.0,
        }
    syntax_score = 1.0

    # check for number of assertions proven
    proof_result_match = re.findall(r"\bproofs:[^\n]*", jasper_out_str)
    if not proof_result_match:
        return {
            "syntax": syntax_score,
            "functionality": 0.0,
            "func_relaxed": 0.0,
        }
    proof_result_list = proof_result_match[-1].split(":")[-1].strip().split(" ")
    # count # of "proven"
    functionality_score = float(proof_result_list.count("proven")) / float(
        len(proof_result_list)
    )
    relaxed_funcality_score = (
        float(proof_result_list.count("proven"))
        + float(proof_result_list.count("undetermined"))
    ) / float(len(proof_result_list))
    return {
        "syntax": syntax_score,
        "functionality": functionality_score,
        "func_relaxed": relaxed_funcality_score,
    }

def find_declarations_yosys(data):
    results = {
        'parameters': [],
        'variables': [],
        'ports': []
    }
    
    if 'modules' not in data:
        return results

    for module_name, module_data in data['modules'].items():
        if 'parameter_default_values' in module_data:
            for param_name, param_value in module_data['parameter_default_values'].items():
                results['parameters'].append({'name': param_name, 'value': param_value})
        
        if 'netnames' in module_data:
            for wire_name, wire_data in module_data['netnames'].items():
                if wire_data['hide_name']:
                    continue

                results['variables'].append({'name': wire_name, 'width': len(wire_data['bits'])})
        
        if 'ports' in module_data:
            for port_name, port_data in module_data['ports'].items():
                results['ports'].append({'name': port_name, 'direction': port_data['direction'], 'width': len(port_data['bits'])})

    return results