"""bench_polish for the rerun (written 2026-10-31; no original polish script was found on the Mac, in
~/FLP or in the two result archives). Faithful minimal version of the procedure described in the paper
(sections/experiments.tex, "SA + polish, CRO + polish") and of the fields read by benchmark_v1/make_tables.py:

  for every sa / cro run in results/bench: take its final layout (real departments), convert it into a
  sequence pair with bench.socp.rects_to_sp, solve ONE Stage-2 SOCP (bench.socp.from_problem, same model
  and margins as our method, cf. bench/methods/ours_s2.py), check with the independent evaluator
  flp.evaluate; keep the SOCP layout only if it is feasible and cheaper by more than 1e-8 relative,
  otherwise keep the original layout.
Output: results/bench_polish/<sa|cro>+polish_<inst>_s<seed>.json with method "sa+polish"/"cro+polish",
cost, feasible, rects, original_cost, polish_time (s, rects_to_sp + SOCP; not part of the budget),
wall = wall of the baseline run, meta.base_file / socp_status / used.  Existing outputs are skipped.
"""
import glob, json, os, sys, time
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from bench.common import problem, check, save          # noqa: E402
from bench.socp import from_problem, rects_to_sp       # noqa: E402

SRC = os.path.join(ROOT, "results", "bench")
OUT = os.path.join(ROOT, "results", "bench_polish")


def main():
    probs, qs = {}, {}
    n_done = n_imp = 0
    for m in ["sa", "cro"]:
        for f in sorted(glob.glob(os.path.join(SRC, f"{m}_*_s*.json"))):
            d = json.load(open(f))
            name = d["instance"]
            fn = os.path.join(OUT, f"{m}+polish_{name}_s{d['seed']}.json")
            if os.path.exists(fn) or d.get("rects") is None:
                continue
            if name not in probs:
                probs[name] = problem(name); qs[name] = from_problem(probs[name])
            prob, q = probs[name], qs[name]
            R0 = np.asarray(d["rects"], float)[:prob.n]
            c0 = d["cost"]
            t0 = time.perf_counter()
            try:
                spair = rects_to_sp(R0)
                o = q.solve_sp(*spair) if spair is not None else dict(status="no sequence pair", rects=None, cost=np.inf)
                status = o["status"]
            except Exception as e:     # overlapping layout etc.
                o = dict(rects=None, cost=np.inf); status = f"error: {e}"
            pt = time.perf_counter() - t0
            used = False; R = R0; ev = None
            if o.get("rects") is not None and np.isfinite(o["cost"]):
                ev1 = check(prob, o["rects"])
                if ev1["feasible"] and (not d["feasible"] or ev1["cost"] < c0 * (1 - 1e-8)):
                    used = True; R = np.asarray(o["rects"]); ev = ev1
            if ev is None:
                ev = check(prob, R)
            rec = dict(method=m + "+polish", instance=name, seed=d["seed"], time_limit=d["time_limit"],
                       wall=d["wall"], polish_time=round(pt, 4), original_cost=c0, original_feasible=d["feasible"],
                       meta=dict(base_file=os.path.relpath(f, ROOT), socp_status=status, used=used),
                       error=None, cost=ev["cost"], feasible=ev["feasible"],
                       violations=[list(map(str, v)) for v in ev["violations"]][:10],
                       rects=[list(map(float, r)) for r in R])
            save(rec, OUT)
            n_done += 1; n_imp += used
    print(f"polished {n_done} runs, SOCP layout used in {n_imp}")


if __name__ == "__main__":
    main()
