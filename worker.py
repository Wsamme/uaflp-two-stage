"""Device-side job queue worker. Jobs are files queue/pending/<method>__<inst>__<seed>__<time>.
Each worker claims (atomic rename) the longest job that still fits before its deadline and runs it via
bench.run. Usage: python3 worker.py <deadline_seconds>; run `python3 worker.py reset` once per call first."""
import os, sys, time, subprocess
Q = os.path.join(os.path.dirname(os.path.abspath(__file__)), "queue")
P, R, D = (os.path.join(Q, s) for s in ("pending", "running", "done"))
for d in (P, R, D): os.makedirs(d, exist_ok=True)
if sys.argv[1] == "reset":
    for f in os.listdir(R): os.rename(os.path.join(R, f), os.path.join(P, f))
    print("pending", len(os.listdir(P)), "done", len(os.listdir(D))); sys.exit()
t_end = time.time() + float(sys.argv[1])
while True:
    left = t_end - time.time()
    jobs = sorted(os.listdir(P), key=lambda f: (-float(f.split("__")[3]), f))
    jobs = [f for f in jobs if float(f.split("__")[3]) + 6 <= left]
    claimed = None
    for f in jobs:
        try:
            os.rename(os.path.join(P, f), os.path.join(R, f)); claimed = f; break
        except OSError:
            continue
    if claimed is None: break
    m, inst, seed, tl = claimed.split("__")
    r = subprocess.run([sys.executable, "-m", "bench.run", "--method", m, "--instances", inst, "--seeds", seed,
                        "--time", tl, "--out", os.path.join(os.path.dirname(Q), "..", "bench2")],
                       capture_output=True, text=True)
    print(r.stdout.strip()[-200:], r.stderr.strip()[-300:], flush=True)
    os.rename(os.path.join(R, claimed), os.path.join(D, claimed))
