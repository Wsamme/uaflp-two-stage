"""Launcher for the ablation-v2 wrappers (written 2026-11-01; NOT part of the original code).
Adds rerun/abl/methods to the bench.methods package path, then runs bench.run unchanged, so
`--method ours_f25` etc. resolve to rerun/abl/methods/ours_f25.py while bench/ stays untouched.
Usage (from flp_run):  .venv\\Scripts\\python.exe rerun\\abl\\run_abl.py --method ours_f25 --instances SC30 --seeds 0 --time 60 --out <dir>
"""
import os, runpy, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
os.chdir(ROOT)
import bench.methods as M
M.__path__.append(os.path.join(HERE, "methods"))
sys.argv = ["bench.run"] + sys.argv[1:]
runpy.run_module("bench.run", run_name="__main__", alter_sys=True)
