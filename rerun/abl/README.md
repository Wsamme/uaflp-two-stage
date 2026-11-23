# rerun/abl/ - ablation v2 on Windows (started 2026-11-01, UTC+8)

Not part of the original code. bench/, flp/, baselines/ and bench/ours_core.py are untouched
(ours_core.py MD5 3907C81380829E5E11C79CA2EEF9BA23, same as the frozen copy).

Files
- `methods/` - new wrappers (`ours_f25`, `ours_f75`, `ours_e2`, `ours_e8`, `ours_esame`, `ours_pn05`, `ours_pn10`,
  `ours_k3`, `ours_k12`, `ours_rst0`, `ours_rst2`, `ours_force`, `ours_nos1_cons`) + `_abl.py` (in-process patches;
  each wrapper's docstring says exactly what differs from `ours`).
- `run_abl.py` - launcher: appends `methods/` to the `bench.methods` package path, then runs `bench.run` unchanged.
- `abl_queue.py` - sequential, resumable queue (same pattern as `rerun\queue_runner.py`), keeps the PC awake.
- `launch.ps1` - starts the queue detached (survives closing the shell).

Outputs
- `results\ablation_v2\bench\<method>_<inst>_s<seed>.json` (standard budgets 20/20/60/60/150 s)
- `results\ablation_v2\du62_600\` (Du62 at 600 s: ours_force, ours_s1, seeds 0-4)
- log `results\ablation_v2\abl_log.txt` (one line per run, incl. meta.stage2 -> watch for "polish only")
- status `results\ablation_v2\abl_status.json` (current job, phase, pid)
- runner stdout/stderr `results\ablation_v2\runner_stdout.txt`, `runner_stderr.txt`
- smoke tests `results\ablation_v2\_smoke\` (not results)

Controls: Windows `ours` seeds 0-9 = `results\bench\ours_*` (same machine, same code). All extra seeds of
`ours` (SC30 10-29, AB20 10-19) are run in this queue.

Job list: phase M (minimal) 160 runs, ~10,760 s; phase F (full plan without SC35) 330 runs, ~23,130 s.
SC35 is NOT included (needs a decision on its filler blocks).

## Resume after a stop / reboot (never start a second runner while one is alive)
    Get-Content -LiteralPath flp_run\results\ablation_v2\abl_status.json
    Get-Process python -ErrorAction SilentlyContinue      # nothing from flp_run should be alive
    cd flp_run
    powershell -ExecutionPolicy Bypass -File rerun\abl\launch.ps1
    # or in the foreground:  .venv\Scripts\python.exe rerun\abl\abl_queue.py
Finished jobs (JSON exists) are skipped; an interrupted run left no JSON and is re-run.
To stop: Stop-Process -Id <pid from abl_status.json> (and its child python).
