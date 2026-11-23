"""Re-run of the ME5001A UA-FLP benchmark on Windows (written 2026-10-31 for the rerun; NOT part of the
original code). Resumable, strictly sequential job queue: one bench.run process at a time.

Job matrix (derived from the original JSONs and ~/FLP/results/bench_work2/queue/done on the Mac):
  phase A  round 2 (340 queue jobs, default env, no OURS_* variables) for sa, cro, then bench_polish,
           then ours, ours_s1, ours_s2, ours_noelite, ours_nos1, ours_unif
           + the round-1-only sa/cro O7 runs (the paper's results/bench = round 1 + round 2, round 2 wins)
  phase B  ga, swap (all 5 instances), construct (all 5, seed 0)
A job is skipped if its JSON already exists, so the runner can be restarted at any time.
Usage:  .venv\\Scripts\\python.exe rerun\\queue_runner.py
"""
import ctypes, json, os, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "results", "bench")
LOG = os.path.join(ROOT, "results", "rerun_log.txt")
STATUS = os.path.join(ROOT, "results", "rerun_status.json")
PY = sys.executable
BUDGET = {"O7": 20, "vC10a": 20, "AB20": 60, "SC30": 60, "Du62": 150}
ALL = ["O7", "vC10a", "AB20", "SC30", "Du62"]
NO_O7 = ["vC10a", "AB20", "SC30", "Du62"]
BIG3 = ["AB20", "SC30", "Du62"]
SEEDS = range(10)


def jobs():
    J = []
    J += [("sa", i, s) for i in ALL for s in SEEDS]          # O7: round 1 only
    J += [("cro", i, s) for i in ALL for s in SEEDS]         # O7: round 1 only
    J.append(("POLISH", None, None))
    for m in ["ours", "ours_s1", "ours_s2"]:
        J += [(m, i, s) for i in ALL for s in SEEDS]
    for m in ["ours_noelite", "ours_nos1", "ours_unif"]:
        J += [(m, i, s) for i in BIG3 for s in SEEDS]
    J += [("ga", i, s) for i in ALL for s in SEEDS]          # vC10a round 2, others round 1
    J += [("swap", i, s) for i in ALL for s in SEEDS]
    J += [("construct", i, 0) for i in ALL]
    return J


def log(msg):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + msg + "\n")


def main():
    os.makedirs(OUT, exist_ok=True)
    try:   # keep the PC awake while the queue runs (ES_CONTINUOUS | ES_SYSTEM_REQUIRED); released on exit
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000001)
    except Exception:
        pass
    J = jobs(); t_start = time.time()
    log(f"runner start pid {os.getpid()}, {len(J)} jobs")
    # numba warm-up (fills the on-disk JIT cache so compile time is not charged to a run's budget)
    wu = os.path.join(ROOT, "results", "_warmup")
    for m in ["sa", "cro", "ga", "swap", "ours", "ours_s2"]:
        if not os.path.exists(os.path.join(wu, f"{m}_O7_s99.json")):
            subprocess.run([PY, "-m", "bench.run", "--method", m, "--instances", "O7", "--seeds", "99",
                            "--time", "3", "--out", wu], cwd=ROOT, capture_output=True, text=True)
            log(f"warm-up {m} done")
    for k, (m, inst, seed) in enumerate(J):
        if m == "POLISH":
            r = subprocess.run([PY, os.path.join(ROOT, "rerun", "polish.py")], cwd=ROOT, capture_output=True, text=True)
            log("polish: " + r.stdout.strip()[-400:] + (" ERR " + r.stderr.strip()[-600:] if r.returncode else ""))
            continue
        fn = os.path.join(OUT, f"{m}_{inst}_s{seed}.json")
        if os.path.exists(fn):
            continue
        json.dump(dict(job=k + 1, total=len(J), current=f"{m} {inst} s{seed}", pid=os.getpid(),
                       runner_start=t_start, now=time.time()), open(STATUS, "w"))
        cmd = [PY, "-m", "bench.run", "--method", m, "--instances", inst, "--seeds", str(seed), "--out", OUT]
        if m != "construct":
            cmd += ["--time", str(float(BUDGET[inst]))]   # as worker.py: time_limit stored as float
        t0 = time.time()
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        tail = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ""
        log(f"[{k + 1}/{len(J)}] {m} {inst} s{seed} rc={r.returncode} {time.time() - t0:.1f}s | {tail}"
            + (" | ERR " + r.stderr.strip()[-500:] if r.returncode or not os.path.exists(fn) else ""))
    json.dump(dict(job=len(J), total=len(J), current="FINISHED", runner_start=t_start, now=time.time()), open(STATUS, "w"))
    log("runner finished")


if __name__ == "__main__":
    main()
