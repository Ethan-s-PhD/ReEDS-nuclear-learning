"""nlpaper: the shared helper package of the nuclear-learning analysis notebooks.

The notebooks under ``z-ethan/notebooks`` import this package for paths, the
house plot style, figure composition and the PRIS loader.

Submodules load lazily. ``import nlpaper`` therefore never imports matplotlib
or numba; each dependency loads when a notebook first touches the submodule
that needs it.

Typical first cell of a notebook::

    import nlpaper
    nlpaper.setup(threads=4)            # thread limits + rcParams + version line
    from nlpaper import paths, plotstyle as ps
"""

from __future__ import annotations

import importlib

__all__ = ["paths", "setup", "plotstyle", "compose", "pris_loader"]
__version__ = "1.0.0"


def __getattr__(name):
    # PEP 562 lazy submodule import. `nlpaper.setup` is a callable module, so
    # both `nlpaper.setup(threads=4)` and `nlpaper.setup.notebook_header(...)` work.
    if name in __all__:
        return importlib.import_module(f"{__name__}.{name}")
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return sorted(list(globals()) + __all__)
