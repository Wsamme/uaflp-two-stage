"""Diversity control: 4 Stage-2 runs all from the Stage-1 best layout (no elite diversity); otherwise as ours."""
import bench.ours_core as oc
import bench.methods._abl as A

def solve(prob, seed, time_limit, log=print):
    A.patch_elite_same()
    return oc.run_ours(prob, seed, time_limit, log)
