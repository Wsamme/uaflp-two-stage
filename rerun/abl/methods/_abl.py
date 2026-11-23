"""Helpers for the proposed ablation wrappers. Does NOT modify bench/ours_core.py: every change is made
inside the wrapper process (parameters of run_ours, or a patched copy of one function), so the frozen
code (CODE_MD5_v2.txt) stays valid. Each wrapper documents exactly what differs from `ours`."""
import os, time
import numpy as np
import bench.ours_core as oc


def env(name, default, cast=float):
    v = os.environ.get(name); return default if v is None else cast(v)


def patch_k_near(k):
    """SPSearch.run(gp, gm, time_limit, T0rel=1e-2, T1rel=2e-6, k_near=6, restart_after=None): set k_near."""
    oc.SPSearch.run.__defaults__ = (1e-2, 2e-6, int(k), None)


def patch_restart(period):
    """Stage-1 restart policy: the original restarts from a random genome when cycles % 4 == 3.
    period=0 -> never restart (every cycle continues from the best); period=p -> cycles % p == p-1.
    Implemented as a copy of oc.sts_stage with only that line changed."""
    orig = oc.sts_stage

    def sts_stage(prob, seed, time_limit, log=print, n_iter=None, T0rel=0.05, T1rel=1e-5, init=None, n_elite=4, trace=None):
        from baselines.cro_sts import sts
        rng = np.random.default_rng(seed); sts.seed(int(seed) + 12345)
        areas, Wt, alpha, n = prob.areas_d, prob.Wt_d, prob.alpha_d, prob.n_d
        pen = float(prob.pen)
        if n_iter is None: n_iter = int(10000 * n)
        t0 = time.time(); best = None; cycles = 0; evals = 0; elite = []
        while time.time() - t0 < time_limit or best is None:
            restart = period > 0 and cycles % period == period - 1          # <- the only change
            if best is None or restart:
                if init is not None and best is None:
                    seq, cuts, codes = [np.array(a, np.int64) for a in init]; T0 = T0rel / 4
                else:
                    seq = rng.permutation(n).astype(np.int64); cuts = rng.permutation(n - 1).astype(np.int64)
                    codes = rng.integers(0, 4, n - 1).astype(np.int64); T0 = T0rel
            else:
                seq, cuts, codes = best[0].copy(), best[1].copy(), best[2].copy(); T0 = T0rel / 4
            f, c, _, _ = sts.evaluate(seq, cuts, codes, areas, prob.W, prob.H, Wt, alpha, pen, 0.0)
            scale = c if c > 0 else 1.0
            bs, bc, bd, bcost, _ = oc._sts_sa(seq, cuts, codes, areas, prob.W, prob.H, Wt, alpha, pen,
                                              n_iter, T0 * scale, T1rel * scale, prob.n)
            cycles += 1; evals += n_iter
            if bcost < 1e299:
                if all(abs(bcost - e[3]) > 1e-7 * bcost for e in elite):
                    elite.append((bs.copy(), bc.copy(), bd.copy(), bcost))
                    elite.sort(key=lambda e: e[3]); del elite[n_elite:]
            if bcost < 1e299 and (best is None or bcost < best[3] - 1e-9):
                best = (bs.copy(), bc.copy(), bd.copy(), bcost)
                if trace is not None: trace.add(bcost)
            if best is None and time.time() - t0 > 3 * time_limit + 60: break
        if best is None: return None
        R = sts.decode(best[0], best[1], best[2], areas, prob.W, prob.H)[:prob.n]
        el = [(e[3], sts.decode(e[0], e[1], e[2], areas, prob.W, prob.H)[:prob.n]) for e in elite]
        return dict(seq=best[0], cuts=best[1], codes=best[2], cost=best[3], rects=R, cycles=cycles, evals=evals, elite=el)
    oc.sts_stage = sts_stage
    return orig


def patch_elite_same():
    """Diversity control: Stage 2 gets 4 starts that are all the Stage-1 BEST layout (elite0 x4),
    i.e. the same number of Stage-2 restarts and time split as `ours`, but no diversity."""
    orig = oc.sts_stage

    def sts_stage(*a, **k):
        r = orig(*a, **k)
        if r is not None and r["elite"]:
            r["elite"] = [r["elite"][0]] * len(r["elite"])
        return r
    oc.sts_stage = sts_stage
