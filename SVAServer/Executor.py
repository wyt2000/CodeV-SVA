import os
import subprocess
import tqdm
import saver
import re
from typing import List
from Utils import add_sva_to_tb_equal, add_sva_to_tb_verify, add_sva_to_impl_verify, find_declarations_yosys
import Utils
import json

def extract_sva(sva):
    if ":" not in sva or sva.startswith("property"):
        return sva
    return sva.split(":", 1)[1].strip()

def normalize(sva):
    return re.sub(r'\s+', '', sva)

def run_jaspergold(jg_command: List[str]) -> str:
    try:
        result = subprocess.run(
            jg_command,
            shell=False,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=Utils.config_global['time_limit'],
        )
        report = result.stdout
        state = True
    except subprocess.TimeoutExpired:
        print("JasperGold process timed out.")
        report = "Error: JasperGold process timed out."
        state = False
    except Exception as e:
        print(f"Error running JasperGold: {str(e)}")
        report = f"Error: {str(e)}"
        state = False
    return {"ok": state, "report": report}

def run_yosys(code, work_dir):
    verilog_filepath = os.path.join(work_dir, "temp.v")
    with open(verilog_filepath, 'w') as f:
        f.write(code)
    json_filepath = os.path.join(work_dir, "output.json")
    yosys_script = f"""
    read_verilog {verilog_filepath}
    proc
    write_json {json_filepath}
    """
    script_filepath = os.path.join(work_dir, "script.ys")
    with open(script_filepath, 'w') as f:
        f.write(yosys_script)

    try:
        subprocess.run(['yosys', script_filepath], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=Utils.config_global['time_limit'])
        with open(json_filepath, 'r') as f:
            json_data = f.read()
        state = True
    except subprocess.TimeoutExpired:
        print("Yosys process timed out.")
        json_data = "Error: Yosys process timed out."
        state = False
    except Exception as e:
        print(f"Error running Yosys: {str(e)}")
        json_data = f"Error: {str(e)}"
        state = False
    return {"ok": state, "data": json_data}

def syntax_check(task_data, work_dir):

    def calculate_jg_metric_for_syntax(jasper_out_str: str):
        syntax_error_match = re.findall(r"\[ERROR \(VERI-\d+\)\]", jasper_out_str)
        syntax_error_match2 = re.findall(r"ERROR: problem encountered", jasper_out_str)
        if syntax_error_match or syntax_error_match2:
            return {
                "syntax": False,
            }
        return {
            "syntax": True,
        }

    impl = task_data["impl"]
    sva_path = os.path.join(work_dir, "sva.sva")
    with open(sva_path, "w") as f:
        f.write(impl)
    tcl_file_path = "tcls/syntax_check.tcl"
    tmp_jg_proj_dir = os.path.join(work_dir, "jg_proj")
    jg_command = [
        "jg",
        "-fpv",
        "-batch",
        "-tcl",
        tcl_file_path,
        "-define",
        "SVA_PATH",
        sva_path,
        "-proj",
        tmp_jg_proj_dir,
        "-allow_unsupported_OS",
    ]
    print("Running JasperGold with command:", " ".join(jg_command))
    result = run_jaspergold(jg_command)
    metrics = calculate_jg_metric_for_syntax(result['report'])
    return metrics | result

def coverage_check(task_data, work_dir):
    # 需要 sv, sva, clock, reset
    # Syntax + Correctness + Coverage
    clock = task_data.get("clock", "")
    reset = task_data.get("reset", "")
    sva = task_data.get("sva", "")
    sv = task_data.get("sv", "")
    sva_path = os.path.join(work_dir, "sva.sva")
    sv_path = os.path.join(work_dir, "sv.sv")
    with open(sva_path, "w") as f:
        f.write(sva)
    with open(sv_path, "w") as f:
        f.write(sv)
    tcl_file_path = "tcls/coverage_check.tcl"
    tmp_jg_proj_dir = os.path.join(work_dir, "jg_proj")
    jg_command = [
        "jg",
        "-fpv",
        "-batch",
        "-tcl",
        tcl_file_path,
        "-define",
        "SV_PATH",
        sv_path,
        "-define",
        "SVA_PATH",
        sva_path,
        "-define",
        "CLOCK",
        clock,
        "-define",
        "RESET",
        reset,
        "-proj",
        tmp_jg_proj_dir,
        "-allow_unsupported_OS",
    ]
    print("Running JasperGold with command:", " ".join(jg_command))
    result = run_jaspergold(jg_command)
    return result

def correctness_verify_impl_only(task_data, work_dir):
    # Syntax + Correctness
    # 不需要 tb，sva 直接插入到 impl 里面
    clock          = task_data.get("clock", None)
    reset          = task_data.get("reset", None)
    asrt           = task_data["asrt"]
    impl           = task_data["impl"]
    top_name       = task_data.get("top_name", None)
    reset_polarity = task_data.get("reset_polarity", None)
    try:
        sva = add_sva_to_impl_verify(impl, asrt, top_name, reset, reset_polarity)
    except Exception as err:
        return {"ok": False, "error": str(err)}
    sva_path = os.path.join(work_dir, "sva.sva")
    with open(sva_path, "w") as f:
        f.write(sva)
    tcl_file_path = "tcls/correctness_verify_impl_only.tcl"
    tmp_jg_proj_dir = os.path.join(work_dir, "jg_proj")
    jg_command = [
        "jg",
        "-fpv",
        "-batch",
        "-tcl",
        tcl_file_path,
        "-define",
        "SVA_PATH",
        sva_path,
    ]
    if clock is not None:
        jg_command.extend([
            "-define",
            "CLOCK",
            clock,
        ])
    if reset is not None:
        jg_command.extend([
            "-define",
            "RESET",
            "tb_reset" if reset != "-none" else reset,
        ])
    if top_name is not None:
        jg_command.extend([
            "-define",
            "TOP_NAME",
            top_name,
        ])
    jg_command.extend([
        "-proj",
        tmp_jg_proj_dir,
        "-allow_unsupported_OS",
    ])
    result = run_jaspergold(jg_command)
    metrics = Utils.calculate_jg_metric_for_verify(result['report'])
    return metrics | result

def correctness_verify(task_data, work_dir):
    # Syntax + Correctness
    # 需要 sv, sva, clock, reset
    clock    = task_data.get("clock", None)
    reset    = task_data.get("reset", None)
    tb       = task_data["tb"]
    asrt     = task_data["asrt"]
    impl     = task_data["impl"]
    top_name = task_data.get("top_name", None)
    sva = add_sva_to_tb_verify(tb, asrt)
    sva_path = os.path.join(work_dir, "sva.sva")
    sv_path = os.path.join(work_dir, "sv.sv")
    with open(sva_path, "w") as f:
        f.write(sva)
    with open(sv_path, "w") as f:
        f.write(impl)
    tcl_file_path = "tcls/correctness_verify.tcl"
    tmp_jg_proj_dir = os.path.join(work_dir, "jg_proj")
    jg_command = [
        "jg",
        "-fpv",
        "-batch",
        "-tcl",
        tcl_file_path,
        "-define",
        "SVA_PATH",
        sva_path,
        "-define",
        "SV_PATH",
        sv_path,
    ]
    if clock is not None:
        jg_command.extend([
            "-define",
            "CLOCK",
            clock,
        ])
    if reset is not None:
        jg_command.extend([
            "-define",
            "RESET",
            reset,
        ])
    if top_name is not None:
        jg_command.extend([
            "-define",
            "TOP_NAME",
            top_name,
        ])
    jg_command.extend([
        "-proj",
        tmp_jg_proj_dir,
        "-allow_unsupported_OS",
    ])
    result = run_jaspergold(jg_command)
    metrics = Utils.calculate_jg_metric_for_verify(result['report'])
    return metrics | result

def get_local_params(code):
    params = re.findall(r"localparam\s+(?:\[[^\]]+\]\s+)?(\w+)\s*=", code)
    return [{"name" : p} for p in params]

def infer_signal_list(task_data, work_dir):
    code = task_data['tb']
    yosys_result = run_yosys(code, work_dir)
    if not yosys_result['ok']:
        return ""
    json_data = json.loads(yosys_result['data'])
    results = find_declarations_yosys(json_data)
    signals = []
    signals_ = []
    vis = set()
    for var in results['variables'] + results['parameters'] + get_local_params(code):
        var_name = var['name']
        if var_name in vis: continue
        vis.add(var_name)
        var_width = var.get("width", 1)
        if var_width > 1:
            signals_.append(f"[{var_width-1}:0] {var_name}")
        else:
            signals.append(var_name)
    signals.extend(signals_)
    return ', '.join(signals)

def equality_check_opt(task_data, work_dir):
    if normalize(extract_sva(task_data["asrt"])) == normalize(extract_sva(task_data["ref_asrt"])):
        return {
            "ok": True,
            "syntax": True,
            "functionality": True,
            "func_relaxed": True,
            "report": "String Match Passed.",
        }
    return equality_check(task_data, work_dir)

def equality_check(task_data, work_dir):

    # TODO: add more metrics for other report
    def calculate_jg_metric_for_equal(jasper_out_str: str):
        # check for syntax error
        syntax_error_match = re.findall(r"syntax error", jasper_out_str)
        if syntax_error_match:
            return {
                "syntax": False,
                "functionality": False,
                "func_relaxed": False,
            }

        # check for functionality error
        # match for "Full equivalence" in jaspert output string
        full_equiv_match = re.findall(r"Full equivalence", jasper_out_str)
        partial_equiv_match = re.findall(r"implies", jasper_out_str)
        if not full_equiv_match:
            if not partial_equiv_match:
                return {
                    "syntax": True,
                    "functionality": False,
                    "func_relaxed": False,
                }
            else:
                return {
                    "syntax": True,
                    "functionality": False,
                    "func_relaxed": True,
                }
        return {
            "syntax": True,
            "functionality": True,
            "func_relaxed": True,
        }

    def extract_assertion(sva, key_signal="tb_reset"):
        sva = sva.strip().replace("\n", "")
        sva = sva.split(f"{key_signal})")[-1].strip().split(");")[0].strip()
        return sva
    
    # 需要 asrt, ref_asrt, signal_list
    # Syntax + Equality
    
    # sva = task_data.get("sva", "")
    sva = add_sva_to_tb_equal(
        task_data['tb'],
        task_data['asrt'], 
        task_data['ref_asrt'],
    )
    lm_assertion_text  = extract_assertion(task_data['asrt'], task_data['key_signal'])
    ref_assertion_text = extract_assertion(task_data['ref_asrt'], task_data['key_signal'])

    if task_data.get("signal_list", None) is None:
        task_data["signal_list"] = infer_signal_list(task_data, work_dir)
    signal_list_text = task_data["signal_list"]
    sva_path = os.path.join(work_dir, "sva.sva")
    with open(sva_path, "w") as f:
        f.write(sva)
    tcl_file_path = "tcls/equality_check.tcl"
    tmp_jg_proj_dir = os.path.join(work_dir, "jg_proj")
    jg_command = [
        "jg",
        "-fpv",
        "-batch",
        "-tcl",
        tcl_file_path,
        "-define",
        "SVA_PATH",
        sva_path,
        "-define",
        "LM_ASSERT_TEXT",
        lm_assertion_text,
        "-define",
        "REF_ASSERT_TEXT",
        ref_assertion_text,
        "-define",
        "SIGNAL_LIST",
        signal_list_text,
        "-proj",
        tmp_jg_proj_dir,
        "-allow_unsupported_OS",
    ]
    print("########## Running JasperGold with command:", " ".join(jg_command))
    result = run_jaspergold(jg_command)
    metrics = calculate_jg_metric_for_equal(result['report'])
    return metrics | result

def testbench_generate(task_data, work_dir):
    try:
        impl = task_data["impl"]
        impl_path = os.path.join(work_dir, "impl.v")
        with open(impl_path, "w") as f:
            f.write(impl)
        top_name = Utils.auto_top(impl)
        ports = Utils.extract_golden_ports(impl_path, top_name, Utils.config_global["time_limit"])
        testbench = Utils.get_tb_code(
            top_name,
            *ports
        )
        clk, reset, reset_polarity = Utils.get_clk_and_rst_name(ports[-2], ports[-1])
    except Exception as err:
        return {"ok": False, "error": str(err)}
    return {"ok": True, "testbench": testbench, "top_name": top_name, "clk": clk, "reset": reset, "reset_polarity": reset_polarity}

def yosys_parse(task_data, work_dir):
    impl = task_data["impl"]
    result = run_yosys(impl, work_dir)
    return result


def majority_vote(task_data, work_dir):
    asrts = task_data["asrts"]
    equivalence_classes = []
    if task_data.get("signal_list", None) is None:
        task_data["signal_list"] = infer_signal_list(task_data, work_dir)

    for asrt in asrts:
        found_class = False
        for eq_class in equivalence_classes:
            # Compare the current assertion with the first assertion in the equivalence class
            task_data_ = task_data.copy()
            if normalize(extract_sva(asrt)) == normalize(extract_sva(eq_class[0])):
                # No need to conduct equality check when two asrt are the same under string matching
                eq_class.append(asrt)
                found_class = True
                break
            task_data_["asrt"] = asrt
            task_data_["ref_asrt"] = eq_class[0]
            result = equality_check(task_data_, work_dir)
            if result["ok"] and result["functionality"]:
                eq_class.append(asrt)
                found_class = True
                break
        if not found_class:
            # Create a new equivalence class if no match is found
            equivalence_classes.append([asrt])

    max_class = max(equivalence_classes, key=len, default=[])
    return {"ok": True, "equivalence_classes": equivalence_classes, "vote_result": max_class[0]}