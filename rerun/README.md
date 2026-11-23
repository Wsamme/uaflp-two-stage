# rerun/ - Windows rerun of the ME5001A UA-FLP benchmark (started 2026-10-31 23:28 UTC+8)

Files (new, not part of the original code; original bench/, flp/, baselines/ untouched):
- `queue_runner.py` - strictly sequential, resumable queue (one `bench.run` process at a time). Skips any job
  whose `results\bench\<method>_<inst>_s<seed>.json` exists. Keeps the PC awake (SetThreadExecutionState)
  while it runs. Log: `results\rerun_log.txt`; current job: `results\rerun_status.json`.
- `polish.py` - bench_polish (SA/CRO + one SOCP polish). Run by the queue as job 101 (after all sa/cro runs).
  Skips existing outputs in `results\bench_polish\`.

## Job order (446 entries: 445 runs + 1 polish step)
1. sa x {O7, vC10a, AB20, SC30, Du62} x seeds 0-9 (50)   [O7 = round-1-only in the original]
2. cro x 5 instances x 10 (50)                             [O7 = round-1-only]
3. POLISH (polish.py on all sa/cro JSONs -> results\bench_polish)
4. ours, ours_s1, ours_s2 x 5 instances x 10 (150)
5. ours_noelite, ours_nos1, ours_unif x {AB20, SC30, Du62} x 10 (90)
6. ga, swap x 5 x 10 (100)                                 [vC10a = round 2, others round 1 only]
7. construct x 5, seed 0 (5)
Matrix = round 2 (Mac ~/FLP/results/bench_work2/queue/done, 340 jobs, default env, no OURS_* variables)
+ the round-1-only files (paper's results/bench = round 1 + round 2, round 2 wins on name clashes).
Budgets passed as `--time <float>` exactly like worker.py (O7/vC10a 20 s, AB20/SC30 60 s, Du62 150 s).
Before the queue, each JIT method ran once on O7 seed 99 for 3 s into `results\_warmup` (numba cache).

## Resume after a stop / reboot (never start a second runner while one is alive)
    Get-Process python      # check nothing from flp_run is still running
    cd flp_run
    .venv\Scripts\python.exe rerun\queue_runner.py
A run that was interrupted mid-way left no JSON, so it is simply re-run. To redo polish, delete
`results\bench_polish\` and run `.venv\Scripts\python.exe rerun\polish.py` (untimed, seconds).

## Polish reproduction
No original polish script exists (searched Mac ~/FLP, bench_work*/bench, both result .tgz, benchmark_v1).
`polish.py` follows the paper text (experiments.tex) and the fields make_tables.py reads (method
"sa+polish"/"cro+polish", cost, feasible, original_cost, polish_time, wall = baseline run wall):
rects -> bench.socp.rects_to_sp -> one Stage2.solve_sp (from_problem, same margins as ours) ->
flp.evaluate; keep SOCP layout only if feasible and > 1e-8 relative cheaper, else keep original.
Validated: applied to the ORIGINAL sa/cro JSONs it reproduces every SAPolish/CROPolish macro in the
paper's numbers.tex exactly (best, mean, n improved, median reduction, all 10 instances x method cells).
That reconstruction of the missing original bench_polish is in `results\bench_polish_from_original\bench_polish\` (100 JSONs).

## Deviations vs. original
- Windows 11, RTX laptop / Ryzen 9, Python 3.11, numba 0.61.2 (original: aarch64 Linux VM 4 cores,
  Python 3.10.12, numba 0.68.0, NumPy 2.2.6 same).
- One run at a time here; the original ran 3 runs in parallel on 4 cores (timing per run differs).
- Round-1-only methods (O7 sa/cro, ga/swap non-vC10a, construct) rerun with the round-2 code version.
- results\records\best_*.json in the paper came from separate long record runs (configs not recorded);
  any records written here are only the best protocol run of the rerun and are labeled as such.
