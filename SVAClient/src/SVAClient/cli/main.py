import argparse
import logging
import sys


logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", type=str, help="Task name")
    parser.add_argument("--config", type=str, help="Config path")
    parser.add_argument("--rank", type=int, help="The node id", default=-1)
    parser.add_argument("--num-nodes", type=int, help="Total number of nodes", default=-1)
    parser.add_argument("--generation-path", type=int, help="The path to save generation results", default=None)
    parser.add_argument("--verification-path", type=int, help="The path to save verification results", default=None)
    args = parser.parse_args()

    if args.task == "nl2sva_human":
        from SVAClient.Agent_NL2SVA_Human import Agent
    elif args.task == "nl2sva_machine":
        from SVAClient.Agent_NL2SVA_Machine import Agent
    elif args.task == "nl2sva_human_no_rtl":
        from SVAClient.Agent_NL2SVA_Human_no_rtl import Agent
    else:
        assert False, f"Unknown Task: {args.task}"

    agent = Agent(args.config, args.rank, args.num_nodes, args.generation_path, args.verification_path)
    agent.solve()
