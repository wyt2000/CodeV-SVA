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

def get_design2sva_prompt(problem: str, testbench: str) -> str:
    testbench = testbench.split("assign tb_reset")[0]
    testbench += "assign tb_reset = (reset_ == 1'b0);\n"

    prompt = ""
    prompt += "Here is the design RTL to generate assertions for:\n"
    prompt += problem
    prompt += "\n\n" + "Here is a partial testbench for you to work on:\n"
    prompt += testbench
    prompt += "\n" + f"""Question: generate a single SVA assertion for the given design RTL that is most important to verify.
If necessary, produce any extra code, including wires, registers, and their assignments.

Do NOT use signals from the design RTL, only use the module input signals or internal signals you have added.
Do NOT use any 'initial' blocks. This testbench is not for running RTL simulation but for formal verification.
Do NOT instantiate the design module inside the testbench.

When implementing the assertion, generate a concurrent SVA assertion and do not add code to output an error message string.
Enclose your SystemVerilog code with ```systemverilog and ```. 

For example:
```systemverilog
logic [3:0] a, b;
assign a = c & d;
assign b = c | d;

assert property (@(posedge clk) disable iff (tb_reset)
    (a && b) != 1'b1
);
```
Only output the code snippet and do NOT output anything else.
Remember to output only one assertion.

Answer:"""
    return prompt

def get_design2sva_repeat_prompt(problem: str, testbench: str, num_question_prompts: int) -> str:
    testbench = testbench.split("assign tb_reset")[0]
    testbench += "assign tb_reset = (reset_ == 1'b0);\n"

    prompt = ""
    prompt += "Here is the design RTL to generate assertions for:\n"
    prompt += problem
    prompt += "\n\n" + "Here is a partial testbench for you to work on:\n"
    prompt += testbench
    for _ in range(num_question_prompts):
        prompt += "\n" + f"""Question: generate a single SVA assertion for the given design RTL that is most important to verify.
If necessary, produce any extra code, including wires, registers, and their assignments.

Do NOT use signals from the design RTL, only use the module input signals or internal signals you have added.
Do NOT use any 'initial' blocks. This testbench is not for running RTL simulation but for formal verification.
Do NOT instantiate the design module inside the testbench.

When implementing the assertion, generate a concurrent SVA assertion and do not add code to output an error message string.
Enclose your SystemVerilog code with ```systemverilog and ```. 

For example:
```systemverilog
logic [3:0] a, b;
assign a = c & d;
assign b = c | d;

assert property (@(posedge clk) disable iff (tb_reset)
    (a && b) != 1'b1
);
```
Only output the code snippet and do NOT output anything else.
Remember to output only one assertion.

Answer:"""
    return prompt

def get_specification_prompt(problem: str, code: str) -> str:
    prompt = f"""You are given a natural language hardware design problem together with its Verilog/SystemVerilog code implementation. You need to provide a list of properties as a verification specification for this design. Your properties must be as comprehensive as possible, covering all key aspects of the design. Each property must be atomic and concise, without relying on or coupling with any other property. The properties should NOT involve the module's clock signal or reset signal. The properties you propose should be verifiable by writing a testbench that instantiates the given module. The description should be as high-level and natural as possible, similar to how a verification engineer would write in a specification document, and should avoid mentioning specific code.

Your response should use several "### Property k" sections to separate the properties you propose, like this:


### Property 1
(the 1-st property)

### Property 2
(the 2-nd property)

(...)

### Property n
(the n-th property)


Here are some examples:

[Example 1]

{Few_Shots.SPEC_EXAMPLE_1}


[Example 2]

{Few_Shots.SPEC_EXAMPLE_2}


[Example 3]

{Few_Shots.SPEC_EXAMPLE_3}


[YOUR TASK HERE]

### Natural Language Problem
{problem}

### Code Implementation
```
{code}
```

[Response]
"""
    return prompt

def get_sva2nl_prompt(sva: str, code: str) -> str:
    prompt = f"""You are given a hardware design written in Verilog/SystemVerilog, along with a SystemVerilog Assertion (SVA) that verifies certain properties of the design. Your task is to describe the properties being checked by the SystemVerilog Assertion (SVA) in natural language. The description should be as high-level and natural as possible, similar to how a verification engineer would write in a specification document, and should avoid mentioning specific code or signal names. Your response should only consist of the properties (written in the voice of a verification engineer), without any additional analysis or explanation.

Here are some examples:


[Example 1]

{Few_Shots.SVA2NL_EXAMPLE_1}


[Example 2]

{Few_Shots.SVA2NL_EXAMPLE_2}


[Example 3]

{Few_Shots.SVA2NL_EXAMPLE_3}


[YOUR TASK HERE]

### Hardware Design
```
{code}
```

### SystemVerilog Assertion (SVA)
```
{sva}
```

[Response]
"""
    return prompt

def get_sva2nl_no_dut_prompt(sva: str) -> str:
    prompt = f"""Your task is to describe the properties being checked by the SystemVerilog Assertion (SVA) in natural language. The description should be similar to how a verification engineer would write in a specification document, and should include required signal names (except the clock and reset signals) involved in the SVA. Your response should only consist of the properties (written in the voice of a verification engineer), without any additional analysis or explanation.

Here are some examples:


[Example 1]

{Few_Shots.SVA2NL_EXAMPLE_NO_DUT_1}


[Example 2]

{Few_Shots.SVA2NL_EXAMPLE_NO_DUT_2}


[Example 3]

{Few_Shots.SVA2NL_EXAMPLE_NO_DUT_3}


[Example 4]

{Few_Shots.SVA2NL_EXAMPLE_NO_DUT_4}


[YOUR TASK HERE]

### SystemVerilog Assertion (SVA)
```
{sva}
```

[Response]
"""
    return prompt


def get_sva2nl_machine_prompt(sva: str, code: str) -> str:
    prompt = f"""You are given a SystemVerilog Assertion (SVA) along with an empty testbench. Your task is to give an unambiguous natural-language description of the SVA, preserving all key details such as signal names and operators, but avoiding any mention of signal width information. Your response should only consist of the natural-language description, without any additional analysis or explanation.

Here are some examples:


[Example 1]

{Few_Shots.SVA2NL_MACHINE_EXAMPLE_1}


[Example 2]

{Few_Shots.SVA2NL_MACHINE_EXAMPLE_2}


[Example 3]

{Few_Shots.SVA2NL_MACHINE_EXAMPLE_3}


[YOUR TASK HERE]

### SystemVerilog Assertion (SVA)
```
{sva}
```

### Testbench
```
{code}
```

[Response]
"""
    return prompt

def get_nl2sva_human_with_doc_prompt(**kwargs) -> str:
    prompt = Few_Shots.SVA_TUTORIAL + "\n# Your Task Here\n"
    return prompt + "\n" + get_nl2sva_human_prompt(**kwargs)

def get_nl2sva_machine_with_doc_prompt(**kwargs) -> str:
    prompt = Few_Shots.SVA_TUTORIAL + "\n# Your Task Here\n"
    return prompt + "\n" + get_nl2sva_machine_prompt(**kwargs)

def get_orm_judgement_nl2sva_human_prompt(testbench: str, problem: str, sva: str) -> str:
    prompt = f'''You are given a Verilog/SystemVerilog code snippet, along with a natural-language property to be checked and its corresponding SystemVerilog Assertion (SVA).
Please determine whether the SVA accurately translates the given natural-language property based on the following criteria, assigning a score from 1 to 10 for each:

1. Logical Structure Accuracy: The SVA must preserve the same logical structure as the original property, including the condition and consequence in implications, as well as the relationships among conjunctions, disjunctions, and negations.

2. Signal Consistency: All signals mentioned in the natural-language property must be explicitly represented in the SVA. The SVA must not omit any referenced signals, nor introduce any new signals (parameters excluded) that do not appear in the original description.

3. Code Consistency: For the aspects that are not clearly specified in the natural-language property, the SVA should be translated based on the relevant implementation in the code. The SVA should not introduce newly defined signals to represent unspecified behaviors.

4. Mapping Correctness: The natural-language property's essential components are correctly mapping in SVA. Pay special attention to the following points:
- "An event eventually happens" includes the current cycle, so it should be translated as [0:$] rather than [1:$], or just expressed using `s_eventually`.
- Distinguish between |-> and |=>: 
  |->: Overlapping implication — the RHS is evaluated starting from the same cycle in which the LHS is true.
  |=>: Non-overlapping implication — the RHS is evaluated starting one clock cycle after the LHS is true.
  If the natural-language property does not contain any timing information, the SVA must not use |=>.

Finally, provide an overall accuracy score (1-10) indicating how well the SVA translates the natural-language property across all criteria.

[YOUR TASK HERE]

### Verilog/SystemVerilog Code

```
{testbench}
```

### Natural-Language Property

{problem}

### SystemVerilog Assertion (SVA)

```
{sva}
```

Your answer should be in the following format:

Thought: [Your Answer and the score of each criteria]
Final Score: [Total Score 1-10, strictly follow this format: "Final Score" on one line, followed by a single integer between 1 and 10 after the colon]

'''
    return prompt

def get_specification_prompt_old(problem: str, code: str) -> str:
    prompt = f"""You are given a natural language hardware design problem together with its Verilog/SystemVerilog code implementation. You need to provide a list of properties as a verification specification for this design. Your properties must be as comprehensive as possible, covering all key aspects of the design. Each property must be atomic and concise, without relying on or coupling with any other property. The properties should refer only to the module's input and output signals (excluding clock and reset signals) and must NOT involve any INTERNAL signals. The properties you propose should be verifiable by writing a testbench that instantiates the given module. 

Here are some examples:


[Example 1]

{Few_Shots.SPEC_EXAMPLE_1}


[Example 2]

{Few_Shots.SPEC_EXAMPLE_2}


[Example 3]

{Few_Shots.SPEC_EXAMPLE_3}


[Example 4]

{Few_Shots.SPEC_EXAMPLE_4}


[YOUR TASK HERE]

### Natural Language Problem
{problem}

### Code Implementation
```
{code}
```

[Response]
"""
    return prompt

def get_nl2sva_human_prompt_open_source_code(testbench: str, problem: str, example_type="seq") -> str:
    prompt =  ""
    prompt += "Here is the testbench to perform your translation:\n"
    prompt += testbench
    prompt += "\nQuestion: Create a SVA assertion that checks: "
    prompt += problem + "\n"

    prompt += f"""Do not add code to output an error message string.
Enclose your SVA code with ```systemverilog and ```. Only output the code snippet and do NOT output anything else.

Answer:"""
    return prompt

def get_bug_localization_prompt(spec: str, code: str) -> str:
    prompt = f'''You are a hardware engineer proficient in Verilog. Below I give you a hardware design description and the corresponding code implementation with **1-5 buggy lines**. Your task is to identify the buggy lines. If the error is caused by missing code, please return the lines of code immediately before and after the correct insertion point.
Hint: the buggy lines may not conform to the design description, or has logic/functional error.
Requirements: You should only output all buggy lines in a verilog code block, without any natural-language explanation. The buggy line you identify must be as precise as possible and should not span more than five lines. For example,
```verilog
(1-5 buggy lines)
```

[Design description]

{spec}

[Code implementation]

```verilog
{code}
```
'''
    return prompt

def get_bug_localization_with_ios_prompt(spec: str, code: str, ios: list[str]) -> str:
    prompt = f'''You are a hardware engineer proficient in Verilog. Below I give you a hardware design description, the corresponding code implementation with **1-5 buggy lines**, and several sets of incorrect input/output examples of the code along with their corresponding reference results. 
Your task is to identify the buggy lines. If the error is caused by missing code, please return the lines of code immediately before and after the correct insertion point.
Hint: the buggy lines may not conform to the design description, or has logic/functional error.
Requirements: You should only output all buggy lines in a verilog code block, without any natural-language explanation. The buggy line you identify must be as precise as possible and should not span more than five lines. For example,
```verilog
(1-5 buggy lines)
```

[Design description]

{spec}

[Code implementation]

```verilog
{code}
```

'''
    if len(ios) >= 1:
        prompt += "[Incorrect input/output examples]\n"
    for io in ios:
        prompt += io + "\n"
    return prompt

def get_bug_localization_with_ios_prompt(spec: str, code: str, ios: list[str]) -> str:
    prompt = f'''You are a hardware engineer proficient in Verilog. Below I give you a hardware design description, the corresponding code implementation with **1-5 buggy lines**, and several sets of incorrect input/output examples of the code along with their corresponding reference results. 
Your task is to identify the buggy lines. If the error is caused by missing code, please return the lines of code immediately before and after the correct insertion point.
Hint: the buggy lines may not conform to the design description, or has logic/functional error.
Requirements: You should only output all buggy lines in a verilog code block, without any natural-language explanation. The buggy line you identify must be as precise as possible and should not span more than five lines. For example,
```verilog
(1-5 buggy lines)
```

[Design description]

{spec}

[Code implementation]

```verilog
{code}
```

'''
    if len(ios) >= 1:
        prompt += "[Incorrect input/output examples]\n"
        prompt += "(Data format: 1 bit Sign, 8 bit Exponent, 23 bit Mantissa)\n"
    for io in ios:
        prompt += io + "\n"
    return prompt


def get_bug_localization_io2sva_prompt(spec: str, code: str, ios: list[str]) -> str:
    prompt = f'''You are a hardware engineer proficient in Verilog. Below I give you a hardware design description, the corresponding code implementation with **1-5 buggy lines**, and several sets of incorrect input/output examples of the code along with their corresponding reference results. 
Your task is to analyze the cause of the error based on the I/O behaviors and write a SystemVerilog Assertion (SVA) to check for this error. The SVA should cause the currently buggy code to fail verification, while allowing the correct code to pass verification. Also, the SVA should be sufficiently generalized, derived from the given input/output behaviors, rather than simply checking conformance to those specific input/output examples.
Requirements: You should first provide an analysis of the error, and then present the SVA inside a SystemVerilog code block. For example:

(...Error Analysis...)
```systemverilog
asrt: assert property (
    (a && b) != 1'b1
);
```

[Design description]

{spec}

[Code implementation]

```
{code}
```

'''
    if len(ios) >= 1:
        prompt += "[Incorrect input/output examples]\n"
        prompt += "(Data format: 1 bit Sign, 8 bit Exponent, 23 bit Mantissa)\n"
    for io in ios:
        prompt += io + "\n"
    return prompt

def get_bug_localization_bug2sva_prompt(spec: str, code: str, bug: str) -> str:
    prompt = f'''You are a hardware engineer proficient in Verilog. Below, I provide a hardware design description, a erroneous code implementation, and the corresponding buggy lines.
Your task is to write a SystemVerilog Assertion (SVA) to check for this error. The SVA should cause the erroneous code with the buggy lines to fail verification, while allowing the correct code to pass.
Requirements: You should present the SVA inside a SystemVerilog code block. For example:
```systemverilog
asrt: assert property (
    (a && b) != 1'b1
);
```

[Design description]

{spec}

[Code implementation]

```
{code}
```

[Buggy lines]

```
{bug}
```

'''
    return prompt


def get_bug_localization_with_sva_prompt(spec: str, code: str, sva: str) -> str:
    prompt = f'''You are a hardware engineer proficient in Verilog. Below I give you a hardware design description, the corresponding code implementation with **1-5 buggy lines**, and a SystemVerilog Assertion (SVA) used to verify some properties in the description. The given code implementation fails to pass the SVA verification.
Your task is to identify the buggy lines. If the error is caused by missing code, please return the lines of code immediately before and after the correct insertion point.
Hint: the buggy lines may not conform to the design description, or has logic/functional error.
Requirements: You should only output all buggy lines in a verilog code block, without any natural-language explanation. The buggy line you identify must be as precise as possible and should not span more than five lines. For example,
```verilog
(1-5 buggy lines)
```

[Design description]

{spec}

[Code implementation]

```verilog
{code}
```

[SVA]

```systemverilog
{sva}
```

'''
    return prompt

def get_fixed_rtl_with_sva_prompt(spec: str, code: str, sva: str) -> str:
    prompt = f'''You are a hardware engineer proficient in Verilog. Below I give you a hardware design description, the corresponding code implementation with **1-5 buggy lines**, and a SystemVerilog Assertion (SVA) used to verify some properties in the description. The given code implementation fails to pass the SVA verification.
Your task is to fix the bugs.
Requirements: You should only output the correct design in a verilog code block, without any natural-language explanation. 

[Design description]

{spec}

[Code implementation]

```verilog
{code}
```

[SVA]

```systemverilog
{sva}
```

'''
    return prompt

def get_chinese_translation_prompt(spec: str) -> str:
    prompt = f'''请将以下硬件验证的约束翻译成中文，不改变其原意：
{spec}
你应该只输出中文翻译，不需要任何额外的解释。
'''
    return prompt

def get_english_translation_prompt(spec: str) -> str:
    prompt = f'''Please translate the following hardware specification to English, without modifying the original meaning:
{spec}
Your response should only consist of the English translation, without any additional analysis or explanation.
'''
    return prompt

def get_nl2sva_human_prompt_no_dut(problem: str) -> str:
    prompt = "Create a SVA assertion that checks: "
    prompt += problem + "\n"

    return prompt

def get_nl2sva_human_prompt_no_dut_chinese(problem: str) -> str:
    prompt = "编写一个 SVA 断言来验证以下性质："
    prompt += problem + "\n"

    return prompt

def get_nl2sva_human_prompt_no_dut_with_tbreset(problem: str) -> str:
    prompt =  ""
    prompt += "\nQuestion: Create a SVA assertion that checks: "
    prompt += problem + "\n"

    example = Few_Shots.NL2SVA_HUMAN_EXAMPLE_SEQUENTIAL

    prompt += "You should use `tb_reset` as the disable condition signal. "
    prompt += f"""Do not add code to output an error message string.
Enclose your SVA code with ```systemverilog and ```. Only output the code snippet and do NOT output anything else.

For example,
```systemverilog
{example}
```
Answer:"""
    return prompt

def get_sva2wavedrom_prompt(sva: str) -> str:
    prompt = f"""You are given a SystemVerilog Assertion (SVA). Your task is to use a waveform diagram to represent the constraints corresponding to this SVA. You need to use WaveDrom, a JSON-like language, to draw the waveform diagram.

The WaveDrom script should consists of three parts (Dict):

1. signal (List[Dict]): The `name` of signals and their values in each cycle of the `wave`. p or n for clock signals, 0 and 1 for low and high logic levels, = for a signal with a defined value, x for an unknown value and '.' for keeping the same value as the previous cycle (if a signal's value remains unchanged between two adjacent cycles, use '.' instead of repeating the same value). The `data` field is used to annotate the specific numerical value of a signal, and the `node` field is used to define logical implication between signals in the subsequent edge part.

2. head (Dict): The cycle index shown at the top of the waveform. By default, it starts from 0 and increments by 1 for each cycle ({{ tick: 0, every: 1 }}).

3. edge (List[Str]): Edges between `nodes` of signals, used to represent the implication relationships between signals. Use -> for straight arrows and ~> for curved arrows.

Your response must contain all signals and their logical relationships in the SVA, except the the reset signal `tb_reset`. Your response should only consist of the WaveDrom script in a code block, without any additional analysis or explanation.

Here are some examples:


[Example 1]

{Few_Shots.SVA2WAVEDROM_EXAMPLE_1}


[Example 2]

{Few_Shots.SVA2WAVEDROM_EXAMPLE_2}


[Example 3]

{Few_Shots.SVA2WAVEDROM_EXAMPLE_3}


[Example 4]

{Few_Shots.SVA2WAVEDROM_EXAMPLE_4}


[YOUR TASK HERE]

### SystemVerilog Assertion (SVA)
```
{sva}
```

[Response]
"""
    return prompt

def get_sva2wavedrom_with_nl_tb_prompt(code: str, specification: str, sva: str) -> str:
    prompt = f"""You are given a hardware design written in Verilog/SystemVerilog, along with a natural-language property to be verified for the design, and a SystemVerilog Assertion (SVA) that verifies the property. Your task is to use a waveform diagram to represent the constraints corresponding to the natural-language property and SVA. You need to use WaveDrom, a JSON-like language, to draw the waveform diagram.

The WaveDrom script should consists of three parts (Dict):

1. signal (List[Dict]): The `name` of signals and their values in each cycle of the `wave`. p or n for clock signals, 0 and 1 for low and high logic levels, = for a signal with a defined value, x for an unknown value and '.' for keeping the same value as the previous cycle (if a signal's value remains unchanged between two adjacent cycles, use '.' instead of repeating the same value). The `data` field is used to annotate the specific numerical value of a signal, and the `node` field is used to define logical implication between signals in the subsequent edge part.

2. head (Dict): The cycle index shown at the top of the waveform. By default, it starts from 0 and increments by 1 for each cycle ({{ tick: 0, every: 1 }}).

3. edge (List[Str]): Edges between `nodes` of signals, used to represent the implication relationships between signals. Use -> for straight arrows and ~> for curved arrows.

Your response must contain all signals and their logical relationships in the SVA, except the the reset signal `tb_reset`. Your response should only consist of the WaveDrom script in a code block, without any additional analysis or explanation.

Here are some examples:


[Example 1]

{Few_Shots.SVA2WAVEDROM_WITH_NL_TB_EXAMPLE_1}


[Example 2]

{Few_Shots.SVA2WAVEDROM_WITH_NL_TB_EXAMPLE_2}


[Example 3]

{Few_Shots.SVA2WAVEDROM_WITH_NL_TB_EXAMPLE_3}


[Example 4]

{Few_Shots.SVA2WAVEDROM_WITH_NL_TB_EXAMPLE_4}


[YOUR TASK HERE]

### Hardware Design
```
{code}
```

### Natural-Language Property
{specification}

### SystemVerilog Assertion (SVA)
```
{sva}
```

[Response]
"""
    return prompt

def get_wave2sva_prompt(signals: str):
    prompt = "Based on this image, create a SystemVerilog assertion (SVA) using the following signals:\n"
    prompt += signals + "\n"
    prompt += f"""Your SVA must precisely reflect the relationships between the signals in the waveform of the image.
You should use `tb_reset` as the disable condition signal. Do not add code to output an error message string.
Enclose your SVA code with ```systemverilog and ```. Only output the code snippet and do NOT output anything else.
For example,
```systemverilog
{Few_Shots.NL2SVA_HUMAN_EXAMPLE_SEQUENTIAL}
```
Answer:"""
    return prompt

def get_wave2sva_with_nl_tb_with_signal_names_prompt(specification: str, code: str) -> str:
    prompt =  ""
    prompt += "Here is the testbench to perform your translation:\n"
    prompt += code 
    prompt += "\nQuestion: Create a SVA assertion that checks: "
    prompt += specification + "\n"
    prompt += "We provide a waveform image corresponding to the given natural-language property. Your SVA must precisely reflect the relationships of the signals in the natural-language property and the waveform.\n"
    prompt += """Do not add code to output an error message string.
Enclose your SVA code with ```systemverilog and ```. Only output the code snippet and do NOT output anything else.

You must use the original parameter names from the RTL in the generated SVA.

For example,
```systemverilog
asrt: assert property (@(posedge clk)
    (sig_A && sig_B) != 1'b1
);
```
Answer:"""
    return prompt

def get_wave2sva_with_nl_tb_prompt(specification: str, code: str) -> str:
    prompt =  ""
    prompt += "Here is the testbench to perform your translation:\n"
    prompt += code 
    prompt += "\nQuestion: Create a SVA assertion that checks: "
    prompt += specification + "\n"
    prompt += "We provide a waveform image corresponding to the given natural-language property. Your SVA must precisely reflect the relationships of the signals in the natural-language property and the waveform.\n"
    prompt += """Do not add code to output an error message string.
Enclose your SVA code with ```systemverilog and ```. Only output the code snippet and do NOT output anything else.

For example,
```systemverilog
asrt: assert property (@(posedge clk)
    (sig_A && sig_B) != 1'b1
);
```
Answer:"""
    return prompt

def get_wave2sva_with_nl_tb_for_data_prompt(specification: str, code: str) -> str:
    prompt =  ""
    prompt += "Here is the testbench to perform your translation:\n"
    prompt += code 
    prompt += "\nQuestion: Create a SVA assertion that checks: "
    prompt += specification + " "
    prompt += "You should use `tb_reset` as the disable condition signal.\n"
    prompt += "We provide a waveform image corresponding to the given natural-language property. Your SVA must precisely reflect the relationships of the signals in the natural-language property and the waveform.\n"
    prompt += """Do not add code to output an error message string.
Enclose your SVA code with ```systemverilog and ```. Only output the code snippet and do NOT output anything else.

For example,
```systemverilog
asrt: assert property (@(posedge clk) disable iff (tb_reset)
    (sig_A && sig_B) != 1'b1
);
```
Answer:"""
    return prompt


def get_wave2sva_with_nl_tb_prompt_bk(code: str, specification: str):
    prompt = f"""Here is a hardware design written in Verilog/SystemVerilog, along with a natural-language property to be verified for the design:

### Hardware Design
```
{code}
```

### Natural-Language Property
{specification}

[YOUR TASK HERE]

"""
    prompt += "Here is a waveform image corresponding to the given natural-language property. Based on the property and the image, create a SystemVerilog assertion (SVA):\n"
    prompt += f"""Your SVA must precisely reflect the relationships of the signals in the natural-language property and the waveform.
Do not add code to output an error message string.
Enclose your SVA code with ```systemverilog and ```. Only output the code snippet and do NOT output anything else.
For example,
```systemverilog
assert property (@(posedge clk)
    (sig_A && sig_B) != 1'b1
);
```
Answer:"""
    return prompt


def get_rewrite_svg_prompt(svg: str, sva: str) -> str:
    prompt = f"""You are given a SystemVerilog Assertion (SVA) and an SVG waveform diagram, and you need to modify this waveform diagram to accurately represent the constraints between signals in the SVA. Arrows are used to indicate implication relationships. You need to ensure that the text size in the waveform diagram is appropriate and does not overlap.
Your modified SVG must contain all signals and their logical relationships in the SVA, except the the reset signal `tb_reset`. Your response should only consist of the SVG in a code block, without any additional analysis or explanation.

[YOUR TASK HERE]

### SystemVerilog Assertion (SVA)
```
{sva}
```

### Waveform Diagram
```svg
{svg}
```

[Response]
"""
    return prompt

def get_sva_tag_prompt(sva: str) -> str:
    prompt = f"""You are a tagging system that provides useful tags for SystemVerilog Assertion (SVAs). Below is an SVA:
[begin]
```systemverilog
{sva}
```
[end]
Please provide coarse-grained tags, such as "Handshake Timing Check" or "Arithmetic Result Verification", to identify main function of above SVA. Your answer should be a list including titles of tags and a brief explanation of each tag. Your response have to strictly follow this JSON format:
[{{"tag": str, "explanation": str}}]. Please response in English."""
    return prompt

def get_orm_judgement_wave2sva_prompt(testbench: str, problem: str, sva: str) -> str:
    prompt = f'''You are a data agent that evaluates whether SystemVerilog Assertions (SVAs) align with natural-language verification properties and waveform diagrams. The input data consists of four components:

1. Verilog/SystemVerilog Code for SVA Verification

2. Natural-Language Verification Property

3. SystemVerilog Assertion (SVA)

4. Waveform Diagram of the SVA

You must analyze the SVA across the following dimensions to determine its consistency with the natural-language description and waveform diagram, assigning a score from 1 to 10 for each:

1. NL-SVA Consistency: The natural-language property and SVA are logically consistent, and all signals and constants mentioned in the natural language are used in the SVA.

2. NL-Waveform Consistency: All information in the natural language property is accurately reflected in the waveform diagram. Redundant information in the waveform is permissible but should be minimal.

3. SVA-Waveform Consistency: The logical relationships between signals shown in the waveform diagram align with those specified in the SVA. Pay attention to ensuring that bit widths remain consistent.

4. Waveform Diagram Quality: The clarity of the waveform diagram, including whether any signal traces or arrows overlap or are missing.

5. Code Consistency: For aspects not explicitly defined in the natural-language property, the SVA should be derived from the relevant implementation in the code. The SVA must not introduce newly defined signals to represent unspecified behaviors.

Your answer should be in the following format:

Thought: [Your Answer and the score of each criteria]
Final Score: [Total Score 1-10, strictly follow this format: "Final Score" on one line, followed by a single integer between 1 and 10 after the colon]

[YOUR TASK HERE]

### Verilog/SystemVerilog Code for SVA Verification

```
{testbench}
```

### Natural-Language Verification Property

{problem}

### SystemVerilog Assertion (SVA)

```
{sva}
```

'''
    return prompt



def get_wave2sva_with_nl_tb_combined_prompt(specification: str, code: str) -> str:
    """Single-stage prompt: Analyze waveform image and generate SVA in one response."""
    prompt = ""
    prompt += "Here is the testbench for context:\n"
    prompt += code
    prompt += "\n\nThe natural-language property to verify is:\n"
    prompt += specification + "\n\n"
    prompt += (
        "We provide a waveform image corresponding to the given natural-language property.\n\n"
        "Your task is to:\n"
        "1. **Analyze the waveform**: Identify the key signals mentioned in the natural-language property. "
        "For each clock cycle (posedge) shown in the waveform, determine the values of all key signals.\n"
        "2. **Generate SVA**: Based on the natural-language property and your signal analysis, create a "
        "SystemVerilog assertion (SVA) that precisely captures the relationships between the signals "
        "described in the property and reflected in the waveform.\n\n"
        "Use the signal values across clock cycles to understand the exact timing and logical relationships, "
        "and translate them into a correct SVA property. Your SVA must precisely reflect the relationships "
        "of the signals in the natural-language property and the waveform.\n\n"
        "Please output your response in the following format:\n\n"
        "(First, output the signal analysis as JSON:)\n"
        "```json\n"
        "{\n"
        '    "cycles": [\n'
        '        {"cycle": 1, "signals": {"<signal_name>": "<value>", ...}},\n'
        '        {"cycle": 2, "signals": {"<signal_name>": "<value>", ...}},\n'
        '        ...\n'
        "    ]\n"
        "}\n"
        "(Then, output the SVA code in the following `assert property ...` format, without any `disable iff`:)\n"
        "```systemverilog\n"
        "asrt: assert property (@(posedge clk)\n"
        "    (sig_A && sig_B) != 1'b1\n"
        ");\n"
        "```\n"
       "Important guidelines:\n"
        "- Focus on signals that are relevant to the natural-language property.\n"
        "- Use the exact signal names as they appear in the waveform and testbench.\n"
        '- For bus signals, use the full bus notation (e.g., "8\'h3b", "4\'b0001", "32\'ha").\n'
        "- If no signals are relevant at a particular cycle, use an empty object: {\"signals\": {}}\n"
        "- Note any important timing relationships, such as delays between signal changes.\n"
        "- Do not add code to output an error message string in the SVA.\n"
        "- Only output the JSON analysis and the SVA code.\n\n"
    )
    return prompt

def get_wave2sva_two_stage_stage1_prompt(specification: str, code: str) -> str:
    """Stage 1: Analyze waveform image to extract key signal values per clock cycle."""
    prompt = ""
    prompt += "Here is the testbench for context:\n"
    prompt += code
    prompt += "\n\nThe natural-language property to verify is:\n"
    prompt += specification + "\n\n"
    prompt += (
        "We provide a waveform image corresponding to the given natural-language property. "
        "Please analyze the waveform image and identify the key signals mentioned in the "
        "natural-language property.\n\n"
        "Your task: For each clock cycle (posedge) shown in the waveform, determine the values "
        "of all key signals at that cycle.\n\n"
        "Please output your analysis in the following JSON format:\n"
        "```json\n"
        "{\n"
        '    "cycles": [\n'
        '        {"cycle": 1, "signals": {"<signal_name>": "<value>", ...}},\n'
        '        {"cycle": 2, "signals": {"<signal_name>": "<value>", ...}},\n'
        '        ...\n'
        "    ]\n"
        "}\n"
        "```\n\n"
        "Important:\n"
        "- Focus on signals that are relevant to the natural-language property.\n"
        "- Use the exact signal names as they appear in the waveform and testbench.\n"
        '- For bus signals, use the full bus notation (e.g., "8\'h3b", "4\'b0001").\n'
        "- If no signals are relevant at a particular cycle, use an empty object: {\"signals\": {}}\n"
        "- Only output the JSON analysis, do NOT output any SVA code or other content.\n"
    )
    return prompt

def get_wave2sva_two_stage_stage2_prompt(specification: str, code: str, signal_analysis: str) -> str:
    """Stage 2: Generate SVA based on natural language property and JSON signal analysis."""
    prompt = ""
    prompt += "Here is the testbench to perform your translation:\n"
    prompt += code
    prompt += "\nQuestion: Create a SVA assertion that checks: "
    prompt += specification + "\n\n"
    prompt += "Below is the signal analysis extracted from the waveform image:\n"
    prompt += "```json\n"
    prompt += signal_analysis + "\n```\n\n"
    prompt += (
        "Based on the natural-language property and the signal analysis above, create a "
        "SystemVerilog assertion (SVA) that precisely captures the relationships between "
        "the signals described in the property and reflected in the signal analysis.\n\n"
        "Use the signal values across clock cycles in the analysis to understand the exact "
        "timing and logical relationships, and translate them into a correct SVA property.\n\n"
        "We also provide the waveform image for additional visual context. Your SVA must "
        "precisely reflect the relationships of the signals in the natural-language property "
        "and the waveform.\n\n"
        "Do not add code to output an error message string.\n"
        "Enclose your SVA code with ```systemverilog and ```. Only output the code snippet "
        "and do NOT output anything else.\n\n"
        "For example,\n"
        "```systemverilog\n"
        "asrt: assert property (@(posedge clk)\n"
        "    (sig_A && sig_B) != 1'b1\n"
        ");\n"
        "```\n"
        "Answer:"
    )
    return prompt


def get_wave2sva_two_stage_stage1_for_data_prompt(specification: str, code: str) -> str:
    """Stage 1 for data: Analyze waveform image to extract key signal values per clock cycle."""
    prompt = ""
    prompt += "Here is the testbench for context:\n"
    prompt += code
    prompt += "\n\nThe natural-language property to verify is:\n"
    prompt += specification + "\n\n"
    prompt += (
        "We provide a waveform image corresponding to the given natural-language property. "
        "Please analyze the waveform image and identify the key signals mentioned in the "
        "natural-language property.\n\n"
        "Your task: For each clock cycle (posedge) shown in the waveform, determine the values "
        "of all key signals at that cycle.\n\n"
        "Please output your analysis in the following JSON format:\n"
        "```json\n"
        "{\n"
        '    "cycles": [\n'
        '        {"cycle": 1, "signals": {"<signal_name>": "<value>", ...}},\n'
        '        {"cycle": 2, "signals": {"<signal_name>": "<value>", ...}},\n'
        '        ...\n'
        "    ]\n"
        "}\n"
        "```\n\n"
        "Important:\n"
        "- Focus on signals that are relevant to the natural-language property.\n"
        "- Use the exact signal names as they appear in the waveform and testbench.\n"
        '- For bus signals, use the full bus notation (e.g., "8\'h3b", "4\'b0001").\n'
        "- If no signals are relevant at a particular cycle, use an empty object: {\"signals\": {}}\n"
        "- Only output the JSON analysis, do NOT output any SVA code or other content.\n"
    )
    return prompt


def get_wave2sva_two_stage_stage2_for_data_prompt(specification: str, code: str, signal_analysis: str) -> str:
    """Stage 2 for data: Generate SVA based on natural language property and JSON signal analysis."""
    prompt = ""
    prompt += "Here is the testbench to perform your translation:\n"
    prompt += code
    prompt += "\nQuestion: Create a SVA assertion that checks: "
    prompt += specification + " "
    prompt += "You should use `tb_reset` as the disable condition signal.\n\n"
    prompt += "Below is the signal analysis extracted from the waveform image:\n"
    prompt += "```json\n"
    prompt += signal_analysis + "\n```\n\n"
    prompt += (
        "Based on the natural-language property and the signal analysis above, create a "
        "SystemVerilog assertion (SVA) that precisely captures the relationships between "
        "the signals described in the property and reflected in the signal analysis.\n\n"
        "Use the signal values across clock cycles in the analysis to understand the exact "
        "timing and logical relationships, and translate them into a correct SVA property.\n\n"
        "We also provide the waveform image for additional visual context. Your SVA must "
        "precisely reflect the relationships of the signals in the natural-language property "
        "and the waveform.\n\n"
        "Do not add code to output an error message string.\n"
        "Enclose your SVA code with ```systemverilog and ```. Only output the code snippet "
        "and do NOT output anything else.\n\n"
        "For example,\n"
        "```systemverilog\n"
        "asrt: assert property (@(posedge clk) disable iff (tb_reset)\n"
        "    (sig_A && sig_B) != 1'b1\n"
        ");\n"
        "```\n"
        "Answer:"
    )
    return prompt
