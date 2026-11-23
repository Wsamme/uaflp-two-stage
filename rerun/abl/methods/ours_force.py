"""Ablation of the budget rule: always run the Stage-2 search (= OURS_FORCE_S2), even if < N_MIN SOCPs fit."""
import bench.ours_core as oc
import bench.methods._abl as A

def solve(prob, seed, time_limit, log=print):
    return oc.run_ours(prob, seed, time_limit, log, budget_rule=False)
