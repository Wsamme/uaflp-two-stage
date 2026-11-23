"""Ablation: Stage 1 gets 75% of the budget (ours: 50%), budget rule OFF.
Why budget_rule=False: with only 25% left for Stage 2 the budget rule's one-shot SOCP probe can fall below
N_MIN=3000 solves (Windows smoke test AB20 s0 at 60 s: probe 10 ms -> 1499 solves -> polish only), which would
turn this variant into 'Stage 1 + polish' and confound the split ablation. Compare with ours_force as well."""
import bench.ours_core as oc
import bench.methods._abl as A

def solve(prob, seed, time_limit, log=print):
    return oc.run_ours(prob, seed, time_limit, log, s1frac=0.75, budget_rule=False)
