"""Ablation: k_near=3 (ours: 6)."""
import bench.ours_core as oc
import bench.methods._abl as A

def solve(prob, seed, time_limit, log=print):
    A.patch_k_near(3)
    return oc.run_ours(prob, seed, time_limit, log)
