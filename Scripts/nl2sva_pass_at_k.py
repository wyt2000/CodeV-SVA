import argparse
import Utils
import json
from collections import defaultdict

def get_pass_at_k_by_key(dataset, key, k=1):
    x = []
    n = 0
    for data_list in dataset.values():
        n = max(n, len(data_list))
        c = sum(int(data[key]) for data in data_list)
        x.append(c)
    return Utils.get_pass_at_k(x, n, k), n

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--n",
        type=int,
        default=1,
        help="Generation Times",
    )
    parser.add_argument(
        "--result-path",
        type=str,
        required=True,
        help="Verification Result Path",
    )
    args = parser.parse_args()
    dataset = defaultdict(list)
    with open(args.result_path) as f:
        for data in f:
            try:
                data = json.loads(data)
            except Exception as err:
                continue
            dataset[data["name"]].append(data)
    
    print(f"Total data count: {len(dataset.keys())}")

    for key in ("syntax", "functionality", "func_relaxed"):
        for k in range(1, args.n + 1):
            pass_at_k, n = get_pass_at_k_by_key(dataset, key, k)
            print(f"{key}@{k}(n={n}): {pass_at_k:.3f}")
