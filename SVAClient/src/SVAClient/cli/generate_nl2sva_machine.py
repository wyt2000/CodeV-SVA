# Copyright 2024 NVIDIA CORPORATION & AFFILIATES
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
from dataclasses import asdict
import os
import re
import pathlib
import random

from openai import OpenAI
import pandas as pd
import tqdm
from SVAClient import Utils 

random.seed(42)

def generate_random_signal(max_int: int = 10):
    # Generate a signal name randomly from sig_A
    # limit to max_int signals
    max_val = min(max_int, 26)
    return f"sig_{chr(random.randint(65, 65 + max_val - 1))}"


def generate_binary_operator():
    # List of operators we can use in assertions
    logical_operators = ["&&", "||", "^"]
    relational_operators = ["<=", ">=", "<", ">"]
    equivalence_operator = ["===", "!=="]
    # weighted random choice
    knob = random.random()
    if knob < 0.5:
        return f"{random.choice(logical_operators)}"
    elif knob < 0.9:
        return f"{random.choice(equivalence_operator)}"
    else:
        return f"{random.choice(relational_operators)}"


def generate_unary_operator():
    # List of operators we can use in assertions
    operators = ["!", "~", "&", "~&", "|", "~|", "^", "~^"]
    return f"{random.choice(operators)}"


def generate_special_operator():
    # List of operators we can use in assertions
    operators = ["$stable", "$rose", "$fell", "$changed", "$past"]
    random_choice = random.choice(operators)
    return random_choice, random_choice == "$past"


def generate_temporal_operator():
    # Temporal operators are a bit different and are used specifically
    operators = ["|->", "|=>"]
    return f"{random.choice(operators)}"


def generate_temporal_bound():
    # Temporal operators are a bit different and are used specifically
    knob = random.random()
    start = random.randint(1, 5)
    end = start + random.randint(1, 5)
    # if knob < 0.01:
    #     return f"##[{start}:$]"
    if knob < 0.3:
        return f"##[{start}:{end}]"
    else:
        return f"##{start}"


def generate_s_temporal_operator():
    # Temporal operators are a bit different and are used specifically
    operators = ["s_eventually", "until", "always", "strong"]
    random_choice = random.choice(operators)
    return random_choice, random_choice == "strong"


def choose_from_unary(depth: int):
    random_val = random.random()
    if random_val < 0.8:
        # Generate simple singal
        return "signal"
    else:
        # Generate a unary operator
        return f"{generate_unary_operator()}signal"


def choose_from_binary(depth: int, max_depth=3):
    # Generate a binary operator
    binary_operator = generate_binary_operator()
    if (
        binary_operator == "==="
        or binary_operator == "!=="
        or binary_operator == "=="
        or binary_operator == "!="
    ) and random.random() < 0.5:
        return f"({generate_expression(depth + 1, max_depth=max_depth)} {binary_operator} 1'b1)"
    else:
        return f"({generate_expression(depth + 1, max_depth=max_depth)} {binary_operator} {generate_expression(depth + 1, max_depth=max_depth)})"


def choose_from_temporal(depth: int, max_depth=3):
    if random.random() < 0.7:
        # Generate a temporal operator
        expr = generate_temporal_operator()
        if expr == "|->":
            temporal_bound = generate_temporal_bound()
            expr = f"{expr} {temporal_bound}"
        return f"{generate_expression(depth + 1)} {expr} {generate_expression(depth + 1, max_depth=max_depth)}"
    elif random.random() < 0.5:
        # Generate a s_temporal operator
        expr, extra_args = generate_s_temporal_operator()
        if extra_args:
            expr = (
                f"{expr}(##[0:$] {generate_expression(depth + 1, max_depth=max_depth)})"
            )
        else:
            expr = f"{expr}({generate_expression(depth + 1, max_depth=max_depth)})"
        return f"{generate_expression(depth + 1, max_depth=max_depth)} |-> " + expr
    else:
        # Generate a special operator
        expr, extra_arg = generate_special_operator()
        if extra_arg:
            constant = random.randint(1, 10)
            if random.random() < 0.5:
                return f"{expr}({generate_expression(depth + 1, max_depth=max_depth)}, {constant}) |-> {generate_expression(depth + 1, max_depth=max_depth)}"
            else:
                return f"{generate_expression(depth + 1, max_depth=max_depth)} |-> {expr}({generate_expression(depth + 1, max_depth=max_depth)}, {constant})"
        else:
            if random.random() < 0.5:
                return f"{expr}({generate_expression(depth + 1, max_depth=max_depth)}) |-> {generate_expression(depth + 1, max_depth=max_depth)}"
            else:
                return f"{generate_expression(depth + 1, max_depth=max_depth)} |-> {expr}({generate_expression(depth + 1, max_depth=max_depth)})"


def generate_expression(depth: int = 0, max_depth=3):
    # Base case: Return a simple signal
    is_leaf = random.random() < (1.0 / max_depth) * depth
    if is_leaf:
        return choose_from_unary(depth)
    elif depth == 0:
        if random.random() < 0.5:
            return choose_from_temporal(depth, max_depth=max_depth)
        else:
            return choose_from_binary(depth, max_depth=max_depth)
    else:
        return choose_from_binary(depth, max_depth=max_depth)


def generate_assertion(max_int: int = 10, max_depth=3):
    # Generate a full assertion statement
    expression = generate_expression(max_depth=max_depth)

    # map "signals" to symbolic names
    # count number of sigals in expression
    num_signals = expression.count("signal")
    prev_symbol = ""
    for _ in range(num_signals):
        symbol = generate_random_signal(max_int=max_int)
        while symbol == prev_symbol:
            symbol = generate_random_signal(max_int=max_int)
        expression = expression.replace("signal", symbol, 1)
        prev_symbol = symbol
    return f"assert property(@(posedge clk)\n\t{expression}\n);"


def extract_signals_nl2sva_machine(ground_truth, min_signal_bits=4, max_signal_bits=8):
    signal_list = re.findall(r"\bsig_\w+", ground_truth)
    signal_list = list(sorted(set(signal_list)))
    signal_list_without_width = []
    signal_list_with_width = []
    signal_bits = random.randint(min_signal_bits, max_signal_bits)
    for sig in signal_list:
        if signal_bits > 1:
            signal_list_with_width.append(f"[{signal_bits - 1}:0] {sig}")
        else:
            signal_list_without_width.append(sig)
    signal_list_text = ",".join(signal_list_without_width + signal_list_with_width)
    return signal_list_text


def get_testbench_and_signal_list_for_machine(ground_truth):
    signal_list_str = extract_signals_nl2sva_machine(ground_truth)
    signal_list = signal_list_str.split(",")
    testbench = '''module testbench (
    input clk,
'''
    if signal_list:
        for signal in signal_list[:-1]:
            testbench += f"    input {signal},\n"
        testbench += f"    input {signal_list[-1]}\n"
    testbench += ");\n"
    testbench += "endmodule"
    return testbench, signal_list_str


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, help="The number of assertions")
    parser.add_argument("--save-path", type=str, help="path to save the assertions")

    args = parser.parse_args()
    dataset = []
    with tqdm.tqdm(total=args.count) as pbar:
        for i in range(args.count):
            sva = generate_assertion()
            testbench, signal_list_str = get_testbench_and_signal_list_for_machine(sva)
            dataset.append({
                "name": f"machine_sva_{i}",
                "sva": sva,
                "testbench": testbench,
                "signal_list": signal_list_str,
            })
            pbar.update(1)

    Utils.save_dataset(dataset, args.save_path)

