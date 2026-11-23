"""Ablation: Stage 1 never restarts from a random genome (ours: every 4th cycle)."""
import bench.ours_core as oc
import bench.methods._abl as A

def solve(prob, seed, time_limit, log=print):
    A.patch_restart(0)
    return oc.run_ours(prob, seed, time_limit, log)
