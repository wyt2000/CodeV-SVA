import random
import SVAClient.Few_Shots as Few_Shots
import logging

random.seed(0)

NL2SVA_SYSTEM_PROMPT = "You are an AI assistant tasked with formal verification of register transfer level (RTL) designs.\nYour job is to translate a description of an assertion to concrete SystemVerilog Assertion (SVA) implementation.\n"
DESIGN2SVA_SYSTEM_PROMPT = "You are an AI assistant tasked with formal verification of register transfer level (RTL) designs.\nYour job is to generate a SystemVerilog assertion for the design-under-test provided.\n"

def get_nl2sva_human_prompt(testbench: str, problem: str, example_type="seq") -> str:
    prompt =  ""
    prompt += "Here is the testbench to perform your translation:\n"
    prompt += testbench
    prompt += "\nQuestion: Create a SVA assertion that checks: "
    prompt += problem + "\n"

    if example_type == "seq":
        example = Few_Shots.NL2SVA_HUMAN_EXAMPLE_SEQUENTIAL
    elif example_type == "comb":
        example = Few_Shots.NL2SVA_HUMAN_EXAMPLE_COMBINATORIAL
    elif example_type == "clk_only":
        example = Few_Shots.NL2SVA_HUMAN_EXAMPLE_CLK_ONLY
    else:
        assert False, f"Invalid example_type: {example_type}!"

    if example_type == "seq":
        prompt += "You should use `tb_reset` as the disable condition signal. "
    prompt += f"""Do not add code to output an error message string.
Enclose your SVA code with ```systemverilog and ```. Only output the code snippet and do NOT output anything else.

For example,
```systemverilog
{example}
```
Answer:"""
    return prompt

def get_nl2sva_human_prompt_no_dut(problem: str) -> str:
    prompt = "Create a SVA assertion that checks: "
    prompt += problem + "\n"

    return prompt

def get_nl2sva_machine_prompt(problem: str, testbench: str) -> str:
    prompt =  ""
    prompt += "Here is the testbench to perform your translation:\n"
    prompt += testbench
    prompt += "\nQuestion: Create a SVA assertion that checks: "
    prompt += problem + "\n"
    prompt += """Do not add code to output an error message string.
Enclose your SVA code with ```systemverilog and ```. Only output the code snippet and do NOT output anything else.

For example,
```systemverilog
assert property (@(posedge clk)
    (sig_A && sig_B) != 1'b1
);
```
Answer:"""
    return prompt
