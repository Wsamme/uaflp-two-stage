# rerun/sc35 (SC35 held-out set, 2026-11-01)
Protocol: PROTOCOL.md. Instance file: instances\uaflp\SC35.json (added 2026-11-01).
Start/resume (PowerShell, in flp_run):  powershell -ExecutionPolicy Bypass -File rerun\sc35\launch.ps1
The queue skips every job whose JSON exists, so re-running launch.ps1 resumes. Check that no queue is running first:
  Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Select ProcessId,CommandLine
Progress: results\ablation_v2\sc35\sc35_log.txt and sc35_status.json. Outputs: results\ablation_v2\sc35\d24 (main, sa/cro), d48 (sensitivity).
120 jobs x ~91 s = ~3 h (budget 90 s, see PROTOCOL.md).
