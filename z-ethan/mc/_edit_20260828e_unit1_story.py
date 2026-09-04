# -*- coding: utf-8 -*-
"""Team ruling 2026-08-28: unit-exact accounting RATIFIED — record the physical
identity of each vendor's completed unit 1 in the S5 Step 4 anchoring derivation.

The ruling's two-part justification: (1) the report's own eq. (10) BOAK = 2OAK
derivation, carried through per vendor; (2) each vendor deploys an experimental
SMR in partnership with INL before its first grid-connected build (PRISM-2
preceding the Natrium plant; the experimental reactors built and deployed under
the 2025 executive order), so at the anchor each vendor has exactly one
completed unit and the first grid-connected build is its unit 2 = BOAK.

Markdown-only edit to cell e8044b0e in mc_cost_trajectories.ipynb — no outputs
change, so no re-execution is needed.
"""
import nbformat

NB = "mc_cost_trajectories.ipynb"

OLD = ("In a\nratio-form engine the base must be the inclusive index of the anchor-cost unit.")

NEW = ("In a\nratio-form engine the base must be the inclusive index of the anchor-cost unit.\n"
       "*(Physical identity of the completed unit — team ruling, 2026-08-28: each vendor\n"
       "deploys an experimental SMR in partnership with INL before its first grid-connected\n"
       "build — PRISM-2 preceding the Natrium plant, and the experimental reactors built and\n"
       "deployed under the 2025 executive order — so at the anchor each vendor holds exactly\n"
       "one completed unit, and its first grid-connected build is unit 2, the unit the BOAK\n"
       "estimate prices. Counting that experimental unit is also what reconciles the report's\n"
       "executive-summary naming, which calls the first grid demonstration \"FOAK\": with the\n"
       "experimental unit as unit 1, the 2030 grid builds price at BOAK = 2OAK rather than\n"
       "FOAK. Unit-exact accounting was ratified on this two-part basis — the report's own\n"
       "eq. (10) derivation plus this unit-1 story; the applied-attachment fork in the\n"
       "report's published tables and the dual-convention sensitivity are pinned by QA4/QA4b\n"
       "below and the atb notebook's ST12 exports.)*")


def main():
    nb = nbformat.read(NB, as_version=4)
    cell = next(c for c in nb.cells if c.get("id") == "e8044b0e")
    assert "team ruling, 2026-08-28" not in cell["source"], "already patched"
    assert OLD in cell["source"], "Step 4 anchor sentence not found"
    cell["source"] = cell["source"].replace(OLD, NEW)
    nbformat.write(nb, NB)
    print(f"patched: {NB} (S5 Step 4 unit-1 story added, markdown only)")


if __name__ == "__main__":
    main()
