"""SC35 launcher (written 2026-11-01; NOT part of the original code). Same as rerun/abl/run_abl.py, plus the
SC35 configuration injected into bench.common at run time (bench/ itself stays untouched):
  DUMMIES["SC35"] = 24  -> free area 48 split into 24 blocks of area 2 (no flow, no shape limit), STS view only,
                           as in the Kang13 data file 12SC35.txt (also Laura22 21SC35.txt), same rule as SC30 (17 x 1).
                           Env SC35_DUMMIES overrides k (pre-declared sensitivity check: 48 x 1, ours/ours_s1 only).
  BUDGET["SC35"]  = 90 s (amended 2026-11-01 from 60 s on a timing-only check, see PROTOCOL.md).
Usage (from flp_run): .venv\\Scripts\\python.exe rerun\\sc35\\run_sc35.py --method ours --instances SC35 --seeds 0 --time 90 --out <dir>
"""
import os, runpy, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
os.chdir(ROOT)
import bench.common as C
C.DUMMIES["SC35"] = int(os.environ.get("SC35_DUMMIES", "24"))
C.BUDGET["SC35"] = 90
if "SC35" not in C.INSTANCES:
    C.INSTANCES.append("SC35")
import bench.methods as M
M.__path__.append(os.path.join(ROOT, "rerun", "abl", "methods"))
sys.argv = ["bench.run"] + sys.argv[1:]
runpy.run_module("bench.run", run_name="__main__", alter_sys=True)
