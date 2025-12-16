# copy from codeparrot/apps_metric/utils.py
# https://huggingface.co/spaces/codeparrot/apps_metric/blob/main/utils.py

import json
import multiprocessing
import numpy as np
from tqdm.contrib.concurrent import process_map

from llmkit_data.eval.apps_run import run_test
from llmkit_data.utils.json import write_jsonl
from llmkit_data.std.datasets import extract_code

TIMEOUT = 10


def check_correctness(sample, generation, timeout, debug=False):
    """Check correctness of code generation with a global timeout.
    The global timeout is to catch some extreme/rare cases not handled by the timeouts
    inside `run_test`"""

    def _temp_run(sample, generation, debug, result):
        result.append(run_test(sample, test=generation, debug=debug))

    manager = multiprocessing.Manager()
    result = manager.list()
    p = multiprocessing.Process(
        target=_temp_run, args=(sample, generation, debug, result)
    )
    p.start()
    p.join(timeout=timeout + 1)
    if p.is_alive():
        p.kill()
    if not result:
        in_outs = json.loads(sample["input_output"])
        # consider that all tests failed
        result = [[-1 for i in range(len(in_outs["inputs"]))]]
        if debug:
            print(f"global timeout")
    return result[0]


def test_generation(args, debug=False):
    apps_item, sample = args
    code = extract_code(sample["response"][0]["content"])

    curr_res = [-2]
    try:
        curr_res = check_correctness(apps_item, code, timeout=TIMEOUT, debug=debug)
        if debug:
            print(f"\nSuccessful compilation of task {code}!")
        fixed = []
        for e in curr_res:
            if isinstance(e, np.ndarray):
                e = e.item(0)
            if isinstance(e, np.bool_):
                e = bool(e)
            fixed.append(e)
        curr_res = fixed
        if not np.all(curr_res):
            if debug:
                print(curr_res)
                print(f"Results were not True for all test cases")
    except Exception as e:
        if debug:
            print(f"Compilation failed, test framework exception = {repr(e)}{e}\n")
    finally:
        assert isinstance(curr_res, list)
        problem_result = np.asarray(curr_res)

    return {**sample,
        "code": code,
        "eval_result": bool(np.all(problem_result > 0)),
        "testcase": curr_res
    }


def evaluate_code_samples(code_samples, apps):
    args = []
    for sample in code_samples:
        problem_id = sample["problem_id"]
        args.append((apps["test"][int(problem_id)], sample))

    # Each test requires 2 processes. Running as many task as CPU cores can overload the CPU
    cpu_num = multiprocessing.cpu_count() // 2
    chunksize = max(len(code_samples) // (cpu_num * 5), 1)
    results = process_map(
        test_generation, args, max_workers=cpu_num, chunksize=chunksize
    )
    return results


def evaluate_incorrect_code_samples_again(results, apps, loop_num):
    """
    There are some strange bugs in apps evaluation that cannot be reproduced.
    The observable issue is that the same code will yield different 'eval_result' values.
    Typically, the test framework may encounter an exception or decide that the code has timed out unreasonably.

    This function is an ugly workaround to address this problem:
    If the function returns a timeout result or raises an exception, it will be run twice to verify if the result is consistent.
    The 'loop_num' parameter controls the number of times the function will be retried until the test framework obtains a consistent result.
    """
    maybe_incorrect_lst, correct_lst = [], []
    for item in results:
        if any(x in item["testcase"] for x in (-1, -2)):
            maybe_incorrect_lst.append(item)
        else:
            correct_lst.append(item)

    for _ in range(loop_num):
        if len(maybe_incorrect_lst) == 0:
            break

        new_results = evaluate_code_samples(maybe_incorrect_lst, apps)
        print(f"maybe incorrect lst size: {len(maybe_incorrect_lst)}")
        check_lst = []
        for i in range(len(new_results)):
            old_item, new_item = maybe_incorrect_lst[i], new_results[i]
            old_eval, new_eval = old_item["eval_result"], new_item["eval_result"]
            if old_eval == new_eval:
                correct_lst.append(old_item)
            else:
                check_lst.append(new_item)
                print(old_item["problem_id"], old_eval, new_item["problem_id"], new_eval)

        maybe_incorrect_lst = check_lst

    if len(results) != len(correct_lst):
        write_jsonl(maybe_incorrect_lst, "debug.jsonl")
        # raise ValueError("cannot correctly evaluate codes")
        print("cannot correctly evalute code. see debug.jsonl")
        if len(maybe_incorrect_lst) < 5:
            correct_lst.extend(maybe_incorrect_lst)

    return correct_lst


def evaluate(code_samples, apps):
    results = evaluate_code_samples(code_samples, apps)
    results = evaluate_incorrect_code_samples_again(results, apps, 10)
    return results
