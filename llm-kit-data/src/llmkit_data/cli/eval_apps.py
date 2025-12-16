import argparse
import json

from datasets import load_dataset

from llmkit_data.eval.apps_eval import evaluate
from llmkit_data.eval.passk import pass_at_k
from llmkit_data.utils.json import read_jsonl, write_jsonl


def count_results(results):
    res = {}

    for item in results:
        problem_id = item["problem_id"]
        n, c = res.get(problem_id, (0, 0))
        n += 1
        if item["eval_result"]:
            c += 1
        res[problem_id] = (n, c)

    return res


def apps_split_by_difficulty(results, apps):
    groups = {"total": []}
    for problem_id, nc in results.items():
        difficulty = apps["test"][problem_id]["difficulty"]
        if difficulty not in groups:
            groups[difficulty] = []
        groups[difficulty].append(nc)
        groups["total"].append(nc)

    return groups


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=str, help="samples path")
    parser.add_argument("--out", type=str, help="output path")
    parser.add_argument("--apps", type=str, help="apps path")
    parser.add_argument(
        "--cached",
        action="store_true",
        help="Skip evaluation and calculate pass@k with cached output",
    )
    args = parser.parse_args()

    apps = load_dataset(args.apps)

    if not args.cached:
        samples = list(read_jsonl(args.samples))
        results = evaluate(samples, apps)
        write_jsonl(results, args.out)
    else:
        results = read_jsonl(args.out)

    cnt = count_results(results)
    groups = apps_split_by_difficulty(cnt, apps)
    
    for name, nc_lst in groups.items(): # nc_lst: [(n, c)] where n is sample_num, c is correct_num
        for k in [1, 5, 10]:
            ns, cs = tuple(zip(*nc_lst)) # transpose
            summary = {"difficulty": name, "k": k, "pass@k": pass_at_k(ns, cs, k)}
            print(json.dumps(summary))
