# SC35 held-out protocol (fixed 2026-11-01, before any SC35 run on Windows)

Written after the Claude CLI consultation (CLAUDE_ADVICE.md), before any SC35 objective value from the
Windows machine was seen. (A 20 s box smoke test of `ours` and a 10 s one of `ours_s1` were run only to check that
the code path works; those values are not used anywhere.)

* **Instance.** SC35 (Liu & Meller 2007): floor 16 x 15, 35 departments, area 192, free area 48, Rmax 4.
  Flows from Liu 2004 thesis App. A.3. Checked 2026-11-01: our flows, areas and ratios are **identical** to
  Kang13/12SC35.txt, Kang13-old/12SC35.txt and Laura22/21SC35.txt (54 pairs, 0 differences; flowcheck.py).
  So the published STS values (3978.62 Kang & Chae; 4030.64 Jeong & Chae) are on the same data.
* **Filler blocks (STS view only: Stage 1 of ours, SA, CRO).** 24 blocks of area 2, zero flow, no shape limit,
  as in the Kang13 data file (and Laura22); same rule as SC30 (17 x 1 from the same Kang13 set). Dummies are dropped
  before flp.evaluate; Stage 2 (SOCP) uses no dummies and may put free space anywhere.
  Injected by rerun/sc35/run_sc35.py (bench/ and ours_core.py unchanged).
* **Sensitivity check (pre-declared, appendix only).** 48 blocks of area 1 for ours and ours_s1, seeds 0-9.
  Never used to choose anything.
* **Budget.** ~~60 s~~ **90 s** wall per run, all methods (see amendment below); N_MIN = 3000 budget rule unchanged and the same for all
  variants. Wall time and meta.stage2 ("polish only" or search) are logged per run and reported.
* **Seeds.** 0-9 (the seed protocol of every other instance; SC35 was never run before, so no tuning on these
  seeds is possible). Deviation from Claude's "new seeds" suggestion, explained in CLAUDE_ADVICE.md.
* **Variants / Holm family.** ours vs {ours_s1, ours_s2, ours_noelite, ours_unif, ours_f25, ours_nos1_cons,
  ours_rst0}: 7 paired comparisons (same seed), two-sided Wilcoxon signed-rank (zsplit), Holm over these 7.
  Effect = mean paired delta % (variant vs ours) with 95 % paired-bootstrap CI. Baselines sa, cro (10 seeds) are
  context only, not in the Holm family.
* **Order / machine.** Windows batch-B workstation, strictly sequential, interleaved by seed (all 8 variants of seed s,
  then seed s+1), then the d48 check, then the baselines.
* **Reference values.** Rule "best published value": SC35 3316.77 (BRKGA-LP, Goncalves & Resende 2015, free-form;
  linearised area constraint, reported error <= 0.005 %). Also reported: 3978.62 (best STS with dummies,
  Kang & Chae) and 4030.64 (Jeong & Chae 2026 CRO-STS). (For SC30, 3343.47 is also the lowest published value in
  Jeong & Chae Table 9 / Goncalves & Resende Table 12, so the same rule covers both.) A new best is claimed only
  for an evaluator-verified layout below 3316.77.

## Amendment A1 (2026-11-01 ~21:45 UTC+8, before the queue started): budget 60 s -> 90 s

One Windows smoke run (ours, seed 0, 60 s, d24, output in results/ablation_v2/sc35/_smoke, not used in any
analysis) logged `SOCP 10 ms: 2904 solves < 3000 -> Stage 1 continues, Stage 2 = polish only`. Under the
method's own budget rule (N_MIN = 3000, unchanged) SC35 at 60 s is on the edge: whether Stage 2 searches would
depend on the timing of a single probe solve, so the Stage-2 ablations (s2, noelite, unif, rst0, f25) would be
partly or wholly void, as on Du62. The budget was therefore raised to 90 s (rest ~44 s, threshold 14.7 ms per
solve, ~47 % margin over the observed 10 ms). The decision uses only the timing line (the solve count), as Claude
allowed ("a timing-only check is acceptable"); it does not use the objective value of the smoke run, and no
other parameter changed. Wall time and meta.stage2 are still logged per run, and any polish-only run is reported.
