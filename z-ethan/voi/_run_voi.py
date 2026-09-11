"""Build and execute voi.ipynb headless on the playground-env kernel.

Run with the playground-env python from z-ethan/voi/:

    python _run_voi.py [--force]

--force sets VOI_FORCE=1 so the posterior-summary cache is recomputed even if
its fingerprint matches. Log: exports/_run.log (nbconvert output appended).
Exits non-zero at the first failure.
"""
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
assert HERE.name == "voi", HERE
LOG = HERE / "exports" / "_run.log"
PY = sys.executable
assert "playground-env" in PY, f"run with the playground-env python, not {PY}"
from jupyter_client.kernelspec import KernelSpecManager   # noqa: E402
_ks = KernelSpecManager().get_kernel_spec("python3")
assert "playground-env" in _ks.argv[0], f"kernel 'python3' resolves to {_ks.argv[0]}"

env = dict(os.environ)
if "--force" in sys.argv:
    env["VOI_FORCE"] = "1"


def run(cmd):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"\n$ {' '.join(cmd)}\n")
        f.flush()
        r = subprocess.run(cmd, cwd=HERE, env=env, stdout=f, stderr=subprocess.STDOUT)
    return r.returncode


def stamp(msg):
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


LOG.parent.mkdir(exist_ok=True)
stamp(f"start python={PY} force={'--force' in sys.argv}")
t0 = time.time()
rc = run([PY, "_build_notebook.py"])
if rc:
    stamp(f"FAIL build (rc={rc})")
    sys.exit(rc)
rc = run([PY, "-m", "jupyter", "nbconvert", "--to", "notebook", "--execute", "--inplace", "voi.ipynb",
          "--ExecutePreprocessor.kernel_name=python3", "--ExecutePreprocessor.timeout=7200"])
if rc:
    stamp(f"FAIL execute (rc={rc})")
    sys.exit(rc)
stamp(f"done in {time.time() - t0:.0f} s")
