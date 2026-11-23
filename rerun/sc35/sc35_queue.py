"""SC35 held-out queue on Windows (written 2026-11-01; NOT part of the original code). Pattern of
rerun/abl/abl_queue.py: strictly sequential, resumable (skips a job whose JSON exists), keeps the PC awake.
Protocol fixed before any SC35 run: see rerun/sc35/PROTOCOL.md.
  Phase H: ours + 7 ablations (ours_s1 ours_s2 ours_noelite ours_unif ours_f25 ours_nos1_cons ours_rst0),
           seeds 0-9, 90 s, 24 x 2 dummies, interleaved by seed (all variants of seed s, then seed s+1).
  Phase D: sensitivity, 48 x 1 dummies, ours + ours_s1, seeds 0-9 (appendix only, never used to choose anything).
  Phase B: STS baselines sa + cro, seeds 0-9, 90 s, 24 x 2 dummies (context only, not in the Holm family).
Usage:  .venv\\Scripts\\python.exe rerun\\sc35\\sc35_queue.py
"""
import ctypes, json, os, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
BASE = os.path.join(ROOT, "results", "ablation_v2", "sc35")
OUT = os.path.join(BASE, "d24")
OUT48 = os.path.join(BASE, "d48")
LOG = os.path.join(BASE, "sc35_log.txt")
STATUS = os.path.join(BASE, "sc35_status.json")
PY = sys.executable
RUN = os.path.join(HERE, "run_sc35.py")
VARIANTS = ["ours", "ours_s1", "ours_s2", "ours_noelite", "ours_unif", "ours_f25", "ours_nos1_cons", "ours_rst0"]


def jobs():
    J = []   # (phase, method, seed, dummies, outdir)
    for s in range(10):
        for m in VARIANTS:
            J.append(("H", m, s, 24, OUT))
    for s in range(10):
        for m in ["ours", "ours_s1"]:
            J.append(("D", m, s, 48, OUT48))
    for s in range(10):
        for m in ["sa", "cro"]:
            J.append(("B", m, s, 24, OUT))
    return J


def log(msg):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + msg + "\n")


def main():
    os.makedirs(OUT, exist_ok=True); os.makedirs(OUT48, exist_ok=True)
    try:
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000001)
    except Exception:
        pass
    J = jobs(); t_start = time.time()
    log(f"runner start pid {os.getpid()}, {len(J)} jobs")
    for k, (ph, m, seed, nd, out) in enumerate(J):
        fn = os.path.join(out, f"{m}_SC35_s{seed}.json")
        if os.path.exists(fn):
            continue
        json.dump(dict(job=k + 1, total=len(J), phase=ph, current=f"{m} SC35 s{seed} d{nd}",
                       pid=os.getpid(), runner_start=t_start, now=time.time()), open(STATUS, "w"))
        env = dict(os.environ, SC35_DUMMIES=str(nd))
        cmd = [PY, RUN, "--method", m, "--instances", "SC35", "--seeds", str(seed), "--time", "90", "--out", out]
        t0 = time.time()
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, env=env)
        tail = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ""
        extra = ""
        try:
            meta = json.load(open(fn)).get("meta", {})
            extra = f" | stage2={meta.get('stage2', 'search')} start={meta.get('start', '-')}"
        except Exception:
            pass
        log(f"[{k + 1}/{len(J)}] {ph} {m} SC35 s{seed} d{nd} rc={r.returncode} {time.time() - t0:.1f}s | {tail}{extra}"
            + (" | ERR " + r.stderr.strip()[-500:] if r.returncode or not os.path.exists(fn) else ""))
    json.dump(dict(job=len(J), total=len(J), current="FINISHED", runner_start=t_start, now=time.time()), open(STATUS, "w"))
    log("runner finished")


if __name__ == "__main__":
    main()
