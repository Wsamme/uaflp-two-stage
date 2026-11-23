"""Ablation: elite pool size 2 (ours: 4); otherwise as ours."""
import bench.ours_core as oc
import bench.methods._abl as A

def solve(prob, seed, time_limit, log=print):
    return oc.run_ours(prob, seed, time_limit, log, n_elite=2)
