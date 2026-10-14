import argparse
import logging
import sys


logging.basicConfig(
    level=logging.INFO,
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
    elif args.task == "design2sva":
        from SVAClient.Agent_Design2SVA import Agent
    elif args.task == "design2sva_repeat":
        from SVAClient.Agent_Design2SVA_Repeat import Agent
    elif args.task == "syntax_check":
        from SVAClient.Agent_Syntax_Check import Agent
    elif args.task == "testbench_generation":
        from SVAClient.Agent_TestBench_Generation import Agent
    elif args.task == "testbench_check":
        from SVAClient.Agent_TestBench_Check import Agent
    elif args.task == "spec_generation":
        from SVAClient.Agent_Spec_Generation import Agent
    elif args.task == "spec2sva":
        from SVAClient.Agent_Spec2SVA import Agent
    elif args.task == "sva2nl":
        from SVAClient.Agent_SVA2NL import Agent
    elif args.task == "spec2sva_reasoning":
        from SVAClient.Agent_Spec2SVA_Reasoning import Agent
    elif args.task == "nl2sva_self_verify_machine":
        from SVAClient.Agent_NL2SVA_Self_Verify_Machine import Agent
    elif args.task == "nl2sva_self_verify_human":
        from SVAClient.Agent_NL2SVA_Self_Verify_Human import Agent
    elif args.task == "nl2sva_human_with_doc":
        from SVAClient.Agent_NL2SVA_Human_With_Doc import Agent
    elif args.task == "nl2sva_machine_with_doc":
        from SVAClient.Agent_NL2SVA_Machine_With_Doc import Agent
    elif args.task == "nl2sva_human_orm":
        from SVAClient.Agent_NL2SVA_Human_ORM import Agent
    elif args.task == "nl2sva_human_major_voting":
        from SVAClient.Agent_NL2SVA_Human_Major_Voting import Agent
    elif args.task == "spec2sva_orm":
        from SVAClient.Agent_Spec2SVA_ORM import Agent
    elif args.task == "sva2nl_equiv_recheck":
        from SVAClient.Agent_SVA2NL_Equiv_Recheck import Agent
    elif args.task == "sva2nl_equiv_recheck_machine":
        from SVAClient.Agent_SVA2NL_Equiv_Recheck_Machine import Agent
    elif args.task == "nl2sva_self_verify_rl_infer":
        from SVAClient.Agent_NL2SVA_Self_Verify_RL_Infer import Agent
    elif args.task == "nl2sva_human_rl_eval":
        from SVAClient.Agent_NL2SVA_Human_RL_Eval import Agent
    elif args.task == "sva2nl_machine":
        from SVAClient.Agent_SVA2NL_Machine import Agent
    elif args.task == "spec2sva_machine":
        from SVAClient.Agent_Spec2SVA_Machine import Agent
    elif args.task == "spec2sva_machine_reasoning":
        from SVAClient.Agent_Spec2SVA_Machine_Reasoning import Agent
    elif args.task == "nl2sva_human_no_rtl":
        from SVAClient.Agent_NL2SVA_Human_no_rtl import Agent
    elif args.task == "testbench_check_fixer":
        from SVAClient.Agent_TestBench_Check_for_SVA_Fixer import Agent
    elif args.task == "bug_localization":
        from SVAClient.Agent_Bug_Localization import Agent
    elif args.task == "spec_translation":
        from SVAClient.Agent_Spec_Translation import Agent
    elif args.task == "sva2nl_no_dut":
        from SVAClient.Agent_SVA2NL_no_dut import Agent
    elif args.task == "spec2sva_reasoning_no_dut":
        from SVAClient.Agent_Spec2SVA_Reasoning_no_dut import Agent
    elif args.task == "sva2nl_equiv_recheck_no_dut":
        from SVAClient.Agent_SVA2NL_Equiv_Recheck_no_dut import Agent
    elif args.task == "bug_localization_with_ios":
        from SVAClient.Agent_Bug_Localization_with_ios import Agent
    elif args.task == "bug_localization_io2sva":
        from SVAClient.Agent_Bug_Localization_io2sva import Agent
    elif args.task == "bug_localization_with_sva":
        from SVAClient.Agent_Bug_Localization_with_sva import Agent
    elif args.task == "bug_fix_with_sva":
        from SVAClient.Agent_Bug_Fix_with_sva import Agent
    elif args.task == "bug_localization_bug2sva":
        from SVAClient.Agent_Bug_Localization_bug2sva import Agent
    elif args.task == "sva2wavedrom":
        from SVAClient.Agent_SVA2WaveDrom import Agent
    elif args.task == "sva2wavedrom_with_nltb":
        from SVAClient.Agent_SVA2WaveDrom_With_NLTB import Agent
    elif args.task == "sva2wavedrom_svg":
        from SVAClient.Agent_SVA2WaveDrom_SVG import Agent
    elif args.task == "svg_rewrite":
        from SVAClient.Agent_SVG_Rewrite import Agent
    elif args.task == "wave2sva":
        from SVAClient.Agent_Wave2SVA import Agent
    elif args.task == "wave2sva_equiv_recheck":
        from SVAClient.Agent_Wave2SVA_Equiv_Recheck import Agent
    elif args.task == "wave2sva_with_nltb":
        from SVAClient.Agent_Wave2SVA_With_NLTB import Agent
    elif args.task == "sva_tag":
        from SVAClient.Agent_SVA_Tag import Agent
    elif args.task == "wave2sva_self_verify":
        from SVAClient.Agent_NL2SVA_Self_Verify_Wave2SVA import Agent
    elif args.task == "wave2sva_no_vision":
        from SVAClient.Agent_Wave2SVA_No_Vision import Agent
    elif args.task == "wave2sva_with_nltb_for_data":
        from SVAClient.Agent_Wave2SVA_With_NLTB_for_data import Agent
    elif args.task == "wave2sva_with_nltb_for_data_from_file":
        from SVAClient.Agent_Wave2SVA_With_NLTB_for_data_from_file import Agent
    elif args.task == "wave2sva_orm":
        from SVAClient.Agent_Wave2SVA_ORM import Agent
    elif args.task == "wave2sva_with_nltb_use_signal_names":
        from SVAClient.Agent_Wave2SVA_With_NLTB_use_signal_names import Agent
    elif args.task == "wave2sva_with_nltb_two_stages":
        from SVAClient.Agent_Wave2SVA_With_NLTB_two_stages import Agent
    elif args.task == "wave2sva_with_nltb_two_stages_for_data":
        from SVAClient.Agent_Wave2SVA_With_NLTB_two_stages_for_data import Agent
    elif args.task == "wave2sva_equiv_recheck_two_stage":
        from SVAClient.Agent_Wave2SVA_Equiv_Recheck_two_stage import Agent
    else:
        assert False, f"Unknown Task: {args.task}"

    agent = Agent(args.config, args.rank, args.num_nodes, args.generation_path, args.verification_path)
    agent.solve()
