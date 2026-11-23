"""Ablation: Stage-2 partner from the k nearest with p_near=0.5 (ours: 0.8)."""
import bench.ours_core as oc
import bench.methods._abl as A

def solve(prob, seed, time_limit, log=print):
    return oc.run_ours(prob, seed, time_limit, log, p_near=0.5)
