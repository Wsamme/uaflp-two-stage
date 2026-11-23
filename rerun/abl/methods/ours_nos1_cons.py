"""Stronger 'no Stage 1' control: Stage 2 (SA over sequence pairs + SOCP) for the whole budget, started from the
deterministic constructive layout of bench/methods/construct.py (CORELAP order + flexible bays) instead of a
random sequence pair. If the constructive layout is not aspect-feasible, falls back to random SPs (as ours_nos1)."""
import numpy as np, time
import bench.ours_core as oc
from bench.socp import rects_to_sp
from bench.methods import construct


def solve(prob, seed, time_limit, log=print):
    t0 = time.time(); tr = oc.Trace(t0)
    S = oc.SPSearch(prob, seed, log, trace=tr)
    c0 = construct.solve(prob, seed, time_limit, log)
    R = None if c0.get("rects") is None else np.asarray(c0["rects"], float)[:prob.n]
    gp = gm = None
    if R is not None and c0.get("meta", {}).get("feasible", True):
        gp, gm = rects_to_sp(R); c, _ = S.evaluate(gp, gm)
        if not np.isfinite(c): gp = gm = None
    start = "construct"
    if gp is None:
        start = "random_sp"; gp, gm, c, _, _ = oc.random_feasible_sp(S, time_limit - (time.time() - t0), log)
        if gp is None:
            return {"rects": None, "meta": {"error": "no feasible start", "trace": tr.final()}}
    c, Rb, gp, gm = S.run(gp, gm, max(time_limit - (time.time() - t0), 0.5))
    return {"rects": np.asarray(Rb).tolist(), "meta": dict(start=start, stage2_cost=c, socp_solves=S.nev,
            socp_infeasible=S.ninf, trace=tr.final())}
