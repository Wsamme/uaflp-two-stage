"""Ablation: Stage 1 restarts every 2nd cycle (ours: every 4th)."""
import bench.ours_core as oc
import bench.methods._abl as A

def solve(prob, seed, time_limit, log=print):
    A.patch_restart(2)
    return oc.run_ours(prob, seed, time_limit, log)
