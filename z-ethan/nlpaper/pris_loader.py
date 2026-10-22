"""Re-export of the PRIS unit-list loader that lives beside the ReEDS input generators.

The single copy of the loader is ``z-ethan/mc/pris_loader.py`` (it is used by
``_generate_cap_trajectories.py`` to build the SMR-additions mandate trajectories). This shim
makes it importable as ``nlpaper.pris_loader`` so the notebooks and the generators share one
implementation and one unit list (``z-ethan/mc/rds2_2025_units.csv``).
"""
from __future__ import annotations

import importlib.util as _ilu
import sys as _sys

from .paths import REPO

_SRC = REPO / "z-ethan" / "mc" / "pris_loader.py"
UNITS_CSV = REPO / "z-ethan" / "mc" / "rds2_2025_units.csv"

_spec = _ilu.spec_from_file_location("nlpaper._pris_loader_impl", _SRC)
_mod = _ilu.module_from_spec(_spec)
_sys.modules[_spec.name] = _mod
_spec.loader.exec_module(_mod)

globals().update({k: v for k, v in vars(_mod).items() if not k.startswith("__")})
del _spec, _mod
