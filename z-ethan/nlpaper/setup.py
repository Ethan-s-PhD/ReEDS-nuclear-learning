"""Per-notebook setup: thread limits, the house plot style and a version line.

Call it in the first code cell of every notebook, before numpy-heavy work and
before anything imports numba::

    import nlpaper
    nlpaper.setup(threads=4)

``nlpaper.setup`` is this module, made callable: ``nlpaper.setup(...)`` runs
:func:`setup`.

Why the thread limit matters. The requirement-map fit (notebook 10) and the
bridge-detection calibration run BLAS-backed least squares on small matrices.
With many BLAS threads, the summation order inside those kernels changes, so
the last digits of a result can change between machines. The paper's exports
were produced with 4 BLAS threads; ``setup(threads=4)`` reproduces that.

Determinism. Every stochastic step in the notebooks draws from an explicit
``numpy.random.default_rng(seed)`` whose seed is written in the cell, so no
result depends on ``PYTHONHASHSEED`` or on the order of a Python ``set``.
``setup`` logs this, and ``seed_note`` lets a notebook add its own seed line.
"""

from __future__ import annotations

import os
import platform
import sys
import types
import warnings

_THREAD_VARS = ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
                "NUMEXPR_NUM_THREADS", "NUMBA_NUM_THREADS")
_LIMITER = None  # keeps the threadpoolctl limiter alive for the session


def _set_thread_env(threads: int) -> dict:
    set_now = {}
    for var in _THREAD_VARS:
        if var not in os.environ:
            os.environ[var] = str(threads)
            set_now[var] = str(threads)
    if "numba" in sys.modules and os.environ.get("NUMBA_NUM_THREADS") != str(threads):
        warnings.warn("nlpaper.setup: numba was imported before setup(); "
                      "NUMBA_NUM_THREADS may not take effect. Call setup() first.",
                      stacklevel=3)
    return set_now


def _limit_threadpools(threads: int) -> bool:
    global _LIMITER
    try:
        from threadpoolctl import threadpool_limits
    except ImportError:
        warnings.warn("nlpaper.setup: threadpoolctl is not installed, so BLAS thread "
                      "limits rely on environment variables only. Install the pinned "
                      "environment (z-ethan/environment.yml).", stacklevel=3)
        return False
    _LIMITER = threadpool_limits(limits=threads)
    return True


def setup(threads: int = 4, seed_note: str | None = None, style: bool = True) -> dict:
    """Limit threads, apply the plot style and print one version line.

    threads   : BLAS / OpenMP / numba thread count (the paper used 4).
    seed_note : optional text naming the seeds this notebook uses; printed.
    style     : apply ``nlpaper.plotstyle`` rcParams (default True).

    Returns a dict with the versions and the thread settings, for logging.
    """
    set_now = _set_thread_env(threads)
    limited = _limit_threadpools(threads)

    import numpy as np
    import pandas as pd

    info = {"python": platform.python_version(), "numpy": np.__version__,
            "pandas": pd.__version__, "threads": threads,
            "threadpoolctl": limited, "env_set": set_now}
    if style:
        import matplotlib
        from . import plotstyle
        plotstyle.apply()
        info["matplotlib"] = matplotlib.__version__
    else:
        info["matplotlib"] = sys.modules["matplotlib"].__version__ \
            if "matplotlib" in sys.modules else "not loaded"

    print(f"nlpaper setup: python {info['python']} | numpy {info['numpy']} | "
          f"pandas {info['pandas']} | matplotlib {info['matplotlib']} | "
          f"threads {threads}" + ("" if limited else " (env vars only)"))
    print("determinism: seeds are explicit numpy Generators in each cell; "
          "results do not depend on PYTHONHASHSEED.")
    if seed_note:
        print(f"seeds: {seed_note}")
    info["seed_note"] = seed_note
    return info


class _CallableModule(types.ModuleType):
    def __call__(self, *args, **kwargs):
        return setup(*args, **kwargs)


sys.modules[__name__].__class__ = _CallableModule
