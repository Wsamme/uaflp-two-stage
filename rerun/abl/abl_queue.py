"""Ablation v2 queue on Windows (written 2026-11-01; NOT part of the original code). Same pattern as
rerun/queue_runner.py: strictly sequential (one run at a time), resumable (a job is skipped if its JSON
exists), keeps the PC awake while it runs (SetThreadExecutionState). Original bench/ untouched; the new
wrappers live in rerun/abl/methods and are loaded through rerun/abl/run_abl.py.

Controls: Windows `ours` seeds 0-9 already exist in results\\bench (same machine, same frozen code);
every extra seed of `ours` (10-29) is rerun here.
Phase M (minimal):  ours_force Du62; ours_nos1_cons AB20 SC30 Du62; ours_f25/ours_f75 AB20 SC30 vC10a;
                    ours_esame AB20 SC30 (all seeds 0-9); ours + ours_unif SC30 seeds 10-29.
Phase F (full, no SC35): ours_e2/e8, ours_k3/k12, ours_pn05/pn10 AB20 SC30; ours_rst0/rst2 AB20 SC30 vC10a
                    (seeds 0-9); core 6 (ours s1 s2 noelite nos1 unif) AB20 SC30 seeds 10-19 (SC30 ours/unif
                    10-19 already done in M -> skipped); Du62 at 600 s ours_force + ours_s1 seeds 0-4
                    (separate dir du62_600); ours_noelite + ours_unif O7 vC10a seeds 0-9.
Usage:  .venv\\Scripts\\python.exe rerun\\abl\\abl_queue.py
"""
import ctypes, json, os, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
BASE = os.path.join(ROOT, "results", "ablation_v2")
OUT = os.path.join(BASE, "bench")
OUT600 = os.path.join(BASE, "du62_600")
LOG = os.path.join(BASE, "abl_log.txt")
STATUS = os.path.join(BASE, "abl_status.json")
PY = sys.executable
RUN = os.path.join(HERE, "run_abl.py")
BUDGET = {"O7": 20, "vC10a": 20, "AB20": 60, "SC30": 60, "Du62": 150}
S10 = range(10)


def jobs():
    J = []   # (phase, method, inst, seed, budget, outdir)
    def add(ph, ms, insts, seeds, budget=None, out=OUT):
        for m in ms:
            for i in insts:
                for s in seeds:
                    J.append((ph, m, i, s, float(budget or BUDGET[i]), out))
    add("M", ["ours_force"], ["Du62"], S10)
    add("M", ["ours_nos1_cons"], ["AB20", "SC30", "Du62"], S10)
    add("M", ["ours_f25", "ours_f75"], ["AB20", "SC30", "vC10a"], S10)
    add("M", ["ours_esame"], ["AB20", "SC30"], S10)
    add("M", ["ours", "ours_unif"], ["SC30"], range(10, 30))
    add("F", ["ours_e2", "ours_e8"], ["AB20", "SC30"], S10)
    add("F", ["ours_k3", "ours_k12", "ours_pn05", "ours_pn10"], ["AB20", "SC30"], S10)
    add("F", ["ours_rst0", "ours_rst2"], ["AB20", "SC30", "vC10a"], S10)
    add("F", ["ours", "ours_s1", "ours_s2", "ours_noelite", "ours_nos1", "ours_unif"], ["AB20", "SC30"], range(10, 20))
    add("F", ["ours_force", "ours_s1"], ["Du62"], range(5), budget=600, out=OUT600)
    add("F", ["ours_noelite", "ours_unif"], ["O7", "vC10a"], S10)
    seen = set(); U = []
    for j in J:                       # drop duplicates (SC30 ours/unif 10-19 appear in M and F)
        key = (j[1], j[2], j[3], j[5])
        if key not in seen: seen.add(key); U.append(j)
    return U


def log(msg):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + msg + "\n")


def main():
    os.makedirs(OUT, exist_ok=True); os.makedirs(OUT600, exist_ok=True)
    try:
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000001)
    except Exception:
        pass
    J = jobs(); t_start = time.time()
    nM = sum(1 for j in J if j[0] == "M")
    log(f"runner start pid {os.getpid()}, {len(J)} jobs (M {nM}, F {len(J) - nM})")
    for k, (ph, m, inst, seed, tl, out) in enumerate(J):
        fn = os.path.join(out, f"{m}_{inst}_s{seed}.json")
        if os.path.exists(fn):
            continue
        json.dump(dict(job=k + 1, total=len(J), phase=ph, phase_M_jobs=nM, current=f"{m} {inst} s{seed} {tl:g}s",
                       pid=os.getpid(), runner_start=t_start, now=time.time()), open(STATUS, "w"))
        cmd = [PY, RUN, "--method", m, "--instances", inst, "--seeds", str(seed), "--time", str(tl), "--out", out]
        t0 = time.time()
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        tail = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ""
        extra = ""
        try:
            meta = json.load(open(fn)).get("meta", {})
            extra = f" | stage2={meta.get('stage2', 'search')} start={meta.get('start', '-')}"
        except Exception:
            pass
        log(f"[{k + 1}/{len(J)}] {ph} {m} {inst} s{seed} {tl:g}s rc={r.returncode} {time.time() - t0:.1f}s | {tail}{extra}"
            + (" | ERR " + r.stderr.strip()[-500:] if r.returncode or not os.path.exists(fn) else ""))
    json.dump(dict(job=len(J), total=len(J), current="FINISHED", runner_start=t_start, now=time.time()), open(STATUS, "w"))
    log("runner finished")


if __name__ == "__main__":
    main()
