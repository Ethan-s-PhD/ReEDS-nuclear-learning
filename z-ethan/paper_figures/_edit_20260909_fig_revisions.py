"""Ethan's figure revisions, 2026-09-09 (plan "zesty-purring-breeze") — the paper_figures side.

Marker-based block replacements in `_build_notebooks.py` (the blocks live in
`_edit_20260909_blocks/` so the record is diffable and re-runnable):

  Fig 2  -> f01b (new-nuclear schedule alone) + the financed-capex fans, aj/eo only, shared axis
  Fig 4  -> f04b (SMR only, shadow price x pvf_onm = required reduction in financed capital cost)
  Fig 6  -> w38/w39/w43 display twins (3-point cut, percent, clipped at 100% with a red edge);
            (b) = mask, (c) = demonstration funding; the cliff -> SF24
  Fig 7  -> g03b + f15b (same unit as Fig 4); the survival matrix -> SF48
  SF24   -> two panels: j06 (statutory, percent) + h06 (monetized detail)
  SF48   -> new: g02 shape-survival matrix
  glossary "Financed capex" row + the appendix preamble's stale SF28-30 sentence

Then: `python _build_notebooks.py` (playground-env) and execute both notebooks headless.
Idempotent (refuses to run twice).
"""
import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
BP = HERE / "_build_notebooks.py"
BLOCKS = HERE / "_edit_20260909_blocks"
text = BP.read_text(encoding="utf-8")
if "f01b_new_nuclear_trajectories.png" in text:
    print("already applied")
    raise SystemExit(0)


def block(name):
    return (BLOCKS / f"{name}.txt").read_text(encoding="utf-8")


def replace_between(start, end, new, keep_end=True):
    """Replace text from `start` (inclusive) up to `end` (exclusive) with `new`."""
    global text
    i = text.index(start)
    assert text.count(start) == 1, start
    j = text.index(end, i + len(start))
    assert text.count(end) == 1, end
    text = text[:i] + new + text[j:]


MARK = "    # ---------------------------------------------------------------- "
replace_between(MARK + "Fig 2\n", MARK + "Fig 3\n", block("fig2"))
replace_between(MARK + "Fig 4\n", MARK + "Fig 5\n", block("fig4"))
replace_between(MARK + "Fig 6\n", MARK + "Fig 7\n", block("fig6"))
replace_between(MARK + "Fig 7\n", MARK + "Table 1\n", block("fig7"))
replace_between('    md(r"""\n    ## SF24 —', '    md(r"""\n    ## SF25 —', block("sf24"))

# SF48 goes right before the tables section
anchor = MARK + "ST1-8\n"
assert text.count(anchor) == 1
text = text.replace(anchor, block("sf48") + anchor)

# glossary row
old = ("| **Financed capex** | OCC plus the interest that accrues during the construction years. "
       "Long builds raise it. |")
new = ("| **Financed capex** | OCC plus the interest that accrues during the construction years. "
       "Long builds raise it. It is the cost basis of Fig 2b/c, and the basis on which Fig 4 and "
       "Fig 7 state the required support (the shadow price capitalized over the model's 30-year "
       "evaluation window, in \\$/kW). |")
assert text.count(old) == 1
text = text.replace(old, new)

# appendix preamble: the "last three figures" sentence is stale
old = ("carries a source block naming the notebook and cell that made it. The\n"
       "    last three figures (SF28–30) embed the winner-boundary and NPV-check\n"
       "    exports (the former re-export gap, closed 2026-08-20 at the source\n"
       "    notebooks).")
new = ("carries a source block naming the notebook and cell that made it. SF28–30\n"
       "    embed the winner-boundary and NPV-check exports (the former re-export gap,\n"
       "    closed 2026-08-20 at the source notebooks); SF48 (the shape-survival\n"
       "    matrix, main-text Fig 7a until 2026-09-09) is the newest entry.")
assert text.count(old) == 1, "preamble sentence not found verbatim"
text = text.replace(old, new)

BP.write_text(text, encoding="utf-8")
print("patched _build_notebooks.py: Fig 2/4/6/7, SF24, SF48, glossary, preamble")
