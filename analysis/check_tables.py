"""Recompute Tables 5.1 and 5.2 of the report from the stored run files and compare with the printed values
(analysis/tables_5_1_5_2_expected.json, copied from the report).

    python analysis/check_tables.py

Batch A (main study): results/bench (second round: the method, SA, CRO) and, for the methods that were not
re-run in the second round (Construct, Swap, GA), results/bench_round1. The polish controls SA+P / CRO+P are in
results/windows_rerun/bench_polish_from_original/bench_polish (one SOCP on the final layout of each batch-A run).
"""
import glob, json, os, statistics as st, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = os.path.join(ROOT, "results")
SRC = [("bench", None), ("bench_round1", None),
       ("windows_rerun/bench_polish_from_original/bench_polish", None)]
NAME = {"construct": "Construct", "swap": "Swap", "ga": "GA", "sa": "SA", "cro": "CRO",
        "sa+polish": "SA+P", "cro+polish": "CRO+P", "ours": "Ours"}


def load():
    runs = {}
    for d, _ in SRC:
        for f in sorted(glob.glob(os.path.join(R, d, "*.json"))):
            r = json.load(open(f))
            m = NAME.get(r.get("method"))
            if m is None or r.get("seed", 0) > 9:
                continue
            key = (m, r["instance"])
            runs.setdefault(key, {})
            runs[key].setdefault(d, []).append(r)
    out = {}
    for key, by in runs.items():          # first source that has the configuration wins
        for d, _ in SRC:
            if d in by:
                out[key] = by[d]
                break
    return out


def table_rows():
    exp = json.load(open(os.path.join(ROOT, "analysis", "tables_5_1_5_2_expected.json")))
    return {(e["method"], e["instance"]): (e["feasible"], e["best"], e["mean"]) for e in exp}


def main():
    runs = load()
    rows = table_rows()
    bad = 0
    for key in sorted(rows):
        feas_t, best_t, mean_t = rows[key]
        rs = [r for r in runs.get(key, []) if r.get("feasible")]
        if not rs:
            print("MISSING", key); bad += 1; continue
        costs = [r["cost"] for r in rs]
        best, mean = min(costs), st.mean(costs)
        tol = lambda a, b: abs(a - b) <= 0.006 * max(1.0, 10 ** (len(str(int(b))) - 7)) + 0.00006
        ok = len(rs) == feas_t and tol(best, best_t) and tol(mean, mean_t)
        bad += not ok
        print(f"{'ok ' if ok else 'BAD'} {key[0]:9s} {key[1]:6s} feasible {len(rs):2d}/{feas_t:2d}  "
              f"best {best:14.4f} ({best_t})  mean {mean:14.4f} ({mean_t})")
    print(f"\n{len(rows)} table rows checked, {bad} mismatches")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
