# A two-stage slicing-tree and sequence-pair method for the UA-FLP

Code, instances and stored runs for the ME5001A M.Sc. coursework project
(Department of Mechanical Engineering, National University of Singapore). The report is submitted separately;
the table and figure numbers below refer to it.

The method solves the unequal-area facility layout problem (UA-FLP) in two stages:

1. **Stage 1** anneals on a slicing-tree genome and keeps up to four elite layouts.
2. **Stage 2** turns each elite layout into a sequence pair and continues the search; every candidate is
   sized exactly by a convex second-order cone program (SOCP, solved with Clarabel).

If too few SOCP solves fit into the remaining time, Stage 2 only polishes the final Stage-1 layout with one SOCP.
Every method returns rectangles only; an independent evaluator checks them and recomputes the cost.

## Repository layout

| Path | Content |
|---|---|
| `flp/` | Instance loader and the independent evaluator (`evaluate.py`, tolerance 1e-6). Shares no code with the methods. |
| `bench/` | The method and the baselines behind one interface (`solve(problem, seed, time_limit, log)`). |
| `bench/ours_core.py` | The two-stage method: Stage-1 annealing, elite pool, budget rule, Stage-2 search. |
| `bench/socp.py` | Layout → sequence pair, relation reduction, the SOCP and its safety margins. |
| `bench/methods/` | One file per configuration: `construct`, `swap`, `ga`, `sa`, `cro`, `ours`, and the first ablation variants. |
| `baselines/cro_sts/` | Slicing-tree decoder and my reimplementation of the coral reefs optimisation of Jeong and Chae (2026). |
| `rerun/` | Batch-B experiment code: polish controls (`polish.py`), ablation (`abl/`), held-out SC35 (`sc35/`, with the protocol fixed before the first run), exact MINLP with SCIP (`minlp_scip.py`). |
| `instances/uaflp/` | The six instances (O7, vC10a, AB20, SC30, Du62, SC35) as JSON, each with its provenance. |
| `results/` | One JSON per run: cost from the evaluator, feasibility, rectangles and run metadata. |
| `analysis/` | `check_tables.py` (recomputes Tables 5.1 and 5.2 of the report), the ablation analysis and the figure scripts. |

About 2,400 lines of Python: the evaluator (70), the method (350), the SOCP model (260), the slicing-tree decoder
(210), the five baselines (590), the benchmark runner (220), the experiment code (590) and the exact MINLP model (140).

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# one run of the method on O7 (20 s); prints the evaluator's cost, 131.6532
python -m bench.run --method ours --instances O7 --seeds 0 --out results/_try

# the SA baseline stops at the best slicing layout, 131.6892
python -m bench.run --method sa --instances O7 --seeds 0 --out results/_try

# recompute Tables 5.1 and 5.2 of the report from the stored runs (40 rows, 0 mismatches)
python analysis/check_tables.py
```

Budgets are wall-clock seconds (O7 and vC10a 20 s, AB20 and SC30 60 s, Du62 150 s, SC35 90 s), so the costs of new
runs depend on the machine. Re-running the frozen code on the same machine moved the means by 0.1–0.6 %.

## Which results belong to which part of the report

| Report | Batch | Files |
|---|---|---|
| Tables 5.1–5.3, Figs 5.1–5.2 (main study) | A | `results/bench/` (the method, SA, CRO); `results/bench_round1/` for the methods not re-run in the second round (Construct, Swap, GA). Where both exist, `results/bench/` is used. |
| SA+P and CRO+P rows | A | `results/windows_rerun/bench_polish_from_original/` (one SOCP on the final layout of each batch-A run) |
| Table 5.7, Fig 5.4 (ablation) | B | `results/ablation_v2/bench/`, `results/ablation_v2/du62_600/`; the paired controls are `results/windows_rerun/bench/` (`ours`, seeds 0–9) |
| Table 5.8 (held-out SC35) | B | `results/ablation_v2/sc35/d24/` (24 dummy blocks of area 2); `d48/` is the pre-declared sensitivity check |
| Table 5.5 (exact MINLP, 300 s; O7 3,600 s) | B | `results/windows_rerun/minlp/` |
| Table 5.4, Fig 5.3 (best stored layouts) | D | `results/windows_rerun/records_long/` (longer runs outside the protocol, seeds from 100) |

Machines: batch A ran on a Linux virtual machine (aarch64, 4 cores); batches B and D on a Windows 11 workstation
(AMD Ryzen 9 9955HX3D, 16 cores). Costs from different batches are never compared directly.

## Known gaps

- The raw outputs of the longer MINLP runs of Table 5.6 (20 min to 5 h, 10 November 2026) are not stored here; only
  the 300-s runs and the 3,600-s O7 run are.
- `analysis/analyze_v2.py`, `make_figures.py` and `summarize_minlp.py` are the scripts used during the project and
  still contain the paths of the machine they ran on; set the paths at the top before running them.
- The ablation numbers in the report were produced with 10,000 bootstrap samples; `analyze_v2.py` uses 5,000, so
  individual intervals differ slightly.
- `rerun/minlp_scip.py` needs SCIP through PySCIPOpt, installed separately.

## Use of AI tools

Claude (Anthropic) was used to assist with writing the code, running the experiments, and formatting the report.
The author is responsible for the content, accuracy and quality of this work.
