"""Ablation: Stage 1 gets 25% of the budget (ours: 50%); otherwise as ours."""
import bench.ours_core as oc
import bench.methods._abl as A

def solve(prob, seed, time_limit, log=print):
    return oc.run_ours(prob, seed, time_limit, log, s1frac=0.25)
