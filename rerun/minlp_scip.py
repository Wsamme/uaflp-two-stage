"""Exact convex MINLP for the UA-FLP, solved by SCIP (re-implementation, 2026-11-09).

Model, as described in the v4 paper (Sec. "Methods compared", item MINLP):
  - continuous lower-left corner (x_i, y_i) and size (w_i, h_i) of every department;
  - area  h_i >= A_i / w_i  (convex for w_i > 0);
  - aspect  w_i <= R h_i,  h_i <= R w_i  (linear);
  - containment in the W x H floor;
  - four binaries per department pair (i left of j, j left of i, i below j, j below i), at least one active,
    with big-M disjunctions (M = W in x, M = H in y);
  - absolute-value distances between centroids (two linear inequalities per term), only for pairs with w_ij > 0.
No symmetry breaking and no warm start. One thread, feasibility tolerance 1e-7.

Usage:  python minlp_scip.py <instance> <time_limit_s> <out_dir>
Writes <out_dir>/minlp_<instance>_t<time>.json with status, bounds, nodes, incumbent trajectory and the best layout,
re-checked with the independent evaluator in flp/evaluate.py.
"""
import json
import math
import os
import platform
import sys
import time

import numpy as np
import pyscipopt as ps
from pyscipopt import quicksum

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from flp import evaluate, instance  # noqa: E402


class IncumbentLog(ps.Eventhdlr):
    """Record (time, objective, dual bound) every time SCIP finds a new best solution."""

    def __init__(self):
        super().__init__()
        self.trace = []

    def eventinit(self):
        self.model.catchEvent(ps.SCIP_EVENTTYPE.BESTSOLFOUND, self)

    def eventexit(self):
        self.model.dropEvent(ps.SCIP_EVENTTYPE.BESTSOLFOUND, self)

    def eventexec(self, event):
        m = self.model
        self.trace.append([m.getSolvingTime(), m.getSolObjVal(m.getBestSol()), m.getDualbound()])


def build(inst):
    n, W, H, A, R = inst.n, inst.W, inst.H, inst.areas, inst.shape_value
    assert inst.shape_type == "Rmax"
    m = ps.Model(f"uaflp_{inst.name}")
    x, y, w, h = {}, {}, {}, {}
    for i in range(n):
        wl, wu = math.sqrt(A[i] / R), min(math.sqrt(A[i] * R), W)
        hl, hu = math.sqrt(A[i] / R), min(math.sqrt(A[i] * R), H)
        w[i] = m.addVar(f"w{i}", lb=wl, ub=wu)
        h[i] = m.addVar(f"h{i}", lb=hl, ub=hu)
        x[i] = m.addVar(f"x{i}", lb=0.0, ub=W - wl)
        y[i] = m.addVar(f"y{i}", lb=0.0, ub=H - hl)
        m.addCons(h[i] >= A[i] * w[i] ** -1, f"area{i}")
        m.addCons(w[i] <= R * h[i], f"asp1_{i}")
        m.addCons(h[i] <= R * w[i], f"asp2_{i}")
        m.addCons(x[i] + w[i] <= W, f"inx{i}")
        m.addCons(y[i] + h[i] <= H, f"iny{i}")
    for i in range(n):
        for j in range(i + 1, n):
            l = m.addVar(f"l{i}_{j}", vtype="B")   # i left of j
            r = m.addVar(f"r{i}_{j}", vtype="B")   # j left of i
            b = m.addVar(f"b{i}_{j}", vtype="B")   # i below j
            a = m.addVar(f"a{i}_{j}", vtype="B")   # j below i
            m.addCons(x[i] + w[i] <= x[j] + W * (1 - l))
            m.addCons(x[j] + w[j] <= x[i] + W * (1 - r))
            m.addCons(y[i] + h[i] <= y[j] + H * (1 - b))
            m.addCons(y[j] + h[j] <= y[i] + H * (1 - a))
            m.addCons(l + r + b + a >= 1)
    obj = []
    for i in range(n):
        for j in range(i + 1, n):
            if inst.w[i, j] <= 0:
                continue
            dx = m.addVar(f"dx{i}_{j}", lb=0.0)
            dy = m.addVar(f"dy{i}_{j}", lb=0.0)
            cxi, cxj = x[i] + 0.5 * w[i], x[j] + 0.5 * w[j]
            cyi, cyj = y[i] + 0.5 * h[i], y[j] + 0.5 * h[j]
            m.addCons(dx >= cxi - cxj)
            m.addCons(dx >= cxj - cxi)
            m.addCons(dy >= cyi - cyj)
            m.addCons(dy >= cyj - cyi)
            obj.append(inst.w[i, j] * (dx + dy))
    m.setObjective(quicksum(obj), "minimize")
    return m, (x, y, w, h)


def main():
    name, tlim, out = sys.argv[1], float(sys.argv[2]), sys.argv[3]
    os.makedirs(out, exist_ok=True)
    inst = instance.load(name)
    t0 = time.time()
    m, (x, y, w, h) = build(inst)
    m.setParam("limits/time", tlim)
    m.setParam("parallel/maxnthreads", 1)
    m.setParam("lp/threads", 1)
    m.setParam("numerics/feastol", 1e-7)
    m.setParam("randomization/randomseedshift", 0)
    m.hideOutput(False)
    m.setLogfile(os.path.join(out, f"minlp_{name}_t{int(tlim)}.log"))
    log = IncumbentLog()
    m.includeEventhdlr(log, "inclog", "record incumbents")
    m.optimize()
    status = m.getStatus()
    res = {
        "method": "MINLP", "instance": name, "solver": f"SCIP {m.version()} via PySCIPOpt {ps.__version__}",
        "threads": 1, "time_limit_s": tlim, "feastol": 1e-7, "status": status,
        "solving_time_s": m.getSolvingTime(), "wall_time_s": time.time() - t0,
        "nodes": m.getNTotalNodes(), "dual_bound": m.getDualbound(),
        "n_vars": m.getNVars(), "n_bin": m.getNBinVars(), "n_conss": m.getNConss(),
        "machine": platform.node(), "cpu": platform.processor(), "python": platform.python_version(),
        "trace": log.trace,
    }
    if m.getNSols() > 0:
        s = m.getBestSol()
        rects = [[m.getSolVal(s, x[i]), m.getSolVal(s, y[i]), m.getSolVal(s, w[i]), m.getSolVal(s, h[i])]
                 for i in range(inst.n)]
        ev = evaluate.evaluate(inst, rects)
        res.update(primal_bound=m.getPrimalbound(), gap_pct=100 * m.getGap(), rects=rects,
                   cost=ev["cost"], feasible=ev["feasible"], violations=[list(map(str, v)) for v in ev["violations"]],
                   first_sol_time_s=log.trace[0][0] if log.trace else None)
    else:
        res.update(primal_bound=None, gap_pct=None, rects=None, cost=None, feasible=False, first_sol_time_s=None)
    fn = os.path.join(out, f"minlp_{name}_t{int(tlim)}.json")
    with open(fn, "w") as f:
        json.dump(res, f, indent=1)
    print(name, status, "cost", res["cost"], "feasible", res["feasible"], "dual", res["dual_bound"],
          "gap%", res["gap_pct"], "nodes", res["nodes"], "t", round(res["solving_time_s"], 1))


if __name__ == "__main__":
    main()
