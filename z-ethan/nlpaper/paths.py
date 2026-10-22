"""Every location the analysis reads or writes, relative to the repository root.

The repository root ``REPO`` is the first ancestor of this file that contains
``z-ethan/nlpaper``. No path in the analysis is absolute: a notebook asks this
module for a folder and gets a path under ``REPO`` (or under the ReEDS output
archive, which lives outside the repository).

ReEDS outputs (the 588 ``outputs.h5`` files, 38.8 GB) are not in the
repository. ``reeds_outputs()`` finds the unpacked archive through the
environment variable ``NL_REEDS_OUTPUTS``; without it, the default is a sibling
folder of the repository, ``<REPO>/../nuclear-learning-reeds-outputs``. When
neither exists, the function returns None. In this kit only notebook 01 asks for
the archive, and it skips its archive copy when the archive is absent.
"""

from __future__ import annotations

import os
from pathlib import Path

_HERE = Path(__file__).resolve().parent


def _find_repo(start: Path) -> Path:
    for d in [start, *start.parents]:
        if (d / "z-ethan" / "nlpaper").is_dir():
            return d
    raise RuntimeError(
        f"nlpaper: cannot find the repository root above {start}; "
        "expected a folder that contains z-ethan/nlpaper.")


REPO = _find_repo(_HERE)
ANALYSIS = REPO / "z-ethan"
DATA = ANALYSIS / "data"
RESULTS = ANALYSIS / "results"
FIGS_SI = RESULTS / "figures" / "si"

ENV_OUTPUTS = "NL_REEDS_OUTPUTS"
DEFAULT_OUTPUTS = REPO.parent / "nuclear-learning-reeds-outputs"


def exports(nb: str) -> Path:
    """Folder for the intermediate exports of notebook ``nb`` (created on demand).

    ``nb`` is the notebook's short name, e.g. ``"07_required_support"`` or ``"07"``;
    use the same spelling everywhere a notebook reads another's exports.
    """
    p = RESULTS / "exports" / nb
    p.mkdir(parents=True, exist_ok=True)
    return p


def reeds_inputs() -> Path:
    """The ReEDS ``inputs/`` folder of this fork (the model's own tables)."""
    return REPO / "inputs"


def deflator_path() -> Path:
    """The ReEDS deflator table, ``inputs/financials/deflator.csv``."""
    return REPO / "inputs" / "financials" / "deflator.csv"


def reeds_outputs(quiet: bool = False) -> Path | None:
    """Root of the unpacked ReEDS output archive, or None when it is absent.

    The folder comes from the environment variable ``NL_REEDS_OUTPUTS``; the
    default is ``<REPO>/../nuclear-learning-reeds-outputs``. The archive holds
    ``<batch>/<prefix><case>_outputs.h5`` plus ``manifest.csv``.
    """
    raw = os.environ.get(ENV_OUTPUTS)
    p = Path(raw).expanduser() if raw else DEFAULT_OUTPUTS
    if p.is_dir():
        return p
    if not quiet:
        src = f"${ENV_OUTPUTS}" if raw else "the default location"
        print(f"nlpaper: ReEDS output archive not found at {p} ({src}); "
              "continuing without it.")
    return None


def require(path, produced_by: str) -> Path:
    """Return ``path`` if it exists; otherwise raise an error naming its producer.

    ``produced_by`` names the notebook (or archive) that writes the file, e.g.
    ``"notebook 05_extract_reeds_outputs"``. The message tells the reader what
    to run, instead of a bare FileNotFoundError.
    """
    path = Path(path)
    if not path.exists():
        try:
            shown = path.relative_to(REPO)
        except ValueError:
            shown = path
        raise FileNotFoundError(
            f"Missing input: {shown}\n"
            f"It is produced by {produced_by}. "
            "(z-ethan/notebooks/00_run_all runs every notebook in order.)")
    return path


def rel(path) -> Path:
    """``path`` relative to REPO when it lies inside it (for printing)."""
    path = Path(path)
    try:
        return path.resolve().relative_to(REPO)
    except ValueError:
        return path
