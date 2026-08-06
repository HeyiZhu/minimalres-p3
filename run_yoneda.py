#!/usr/bin/env python3
"""Run a Yoneda product after auto-bootstrapping the data files if needed.

Edit the four variables below, then:  python3 run_yoneda.py
"""

import subprocess, sys, os

# ── configure here ────────────────────────────────────────────────────────────
MD  = 40   # half-max-degree (data files will be named  <MD>_mot_gens, etc.)
LEN = 30    # resolution length  (mr_mot will be run up to this length)
BS  = 4    # beta filtration
BB  = 6    # beta generator index  =>  beta = {BS-BB}
# ─────────────────────────────────────────────────────────────────────────────

DIR = os.path.dirname(os.path.abspath(__file__))

def run(cmd, desc):
    print(f"  {desc} ...", flush=True)
    r = subprocess.run(cmd, cwd=DIR)
    if r.returncode != 0:
        sys.exit(f"FAILED (exit {r.returncode}): {' '.join(str(c) for c in cmd)}")

def need(path):
    return not os.path.isfile(os.path.join(DIR, path))

pre = f"{MD}_"

# Bootstrap: each step is skipped when its sentinel output file already exists.
if need(f"{pre}ex2poly_index"):
    run([f"{DIR}/e2p", str(MD)], f"e2p {MD}")

if need(f"{pre}mot_deltas"):
    run([f"{DIR}/motTab", str(MD)], f"motTab {MD}")

if need(f"{pre}mot_res"):
    # mr_ex length must be strictly greater than LEN
    run([f"{DIR}/mr_ex", str(MD), str(LEN + 1)], f"mr_ex {MD} {LEN+1}")

if need(f"{pre}mot_gens{LEN}"):
    run([f"{DIR}/mr_mot", str(MD), str(LEN)], f"mr_mot {MD} {LEN}")

# Run yoneda
print()
cmd = [f"{DIR}/yoneda", str(MD), str(LEN), str(BS), str(BB)]
print("Running:", " ".join(str(c) for c in cmd))
print()
subprocess.run(cmd, cwd=DIR)
