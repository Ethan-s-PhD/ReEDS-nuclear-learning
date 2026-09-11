"""Fig 6 on one common demonstration-window end, 2038 (Ethan, 2026-09-10).

Patches _build_notebook_v2.py in place (re-runnable):
  * the four duplicated per-schedule window blocks (09-09) collapse to one W_COMMON = 2038 block;
  * u51/u52 window rows "wvoi" become "w2038";
  * w38 (Fig 6a): one dashed line at 2038, no per-schedule lines, no price-range shading;
  * w39 (Fig 6b): share of samples covered by the credit at the 50% statutory maximum only, one
    dashed line at 2038, right-edge labels = share covered in the last build year;
  * w43 (Fig 6c): priced through the common window.
Then rebuild: python _build_notebook_v2.py  and  RD_ANCHORS=5a python _build_notebook_v2.py; execute both.
"""
import re
from pathlib import Path

p = Path(__file__).with_name("_build_notebook_v2.py")
s = p.read_text(encoding="utf-8")
n0 = len(s)

BLOCK_RE = re.compile(
    r'# ---- the demonstration-window end from the decision-value analysis \(voi/, 2026-09-09\) ----\n'
    r'(?:.*\n)*?print\("per-schedule window end \(voi, expected-loss minimizer at rho_g = 1\):", W_VOI\)\n\n')
NEW_BLOCK = '''# ---- the demonstration-window end: one common year (Ethan, 2026-09-10) -------------
# The decision-value analysis (voi/, SF56, ST19) found that graduation is essentially complete
# by 2038 in every schedule at both ceilings (voi p36_common_window_table.csv; eia builds only
# from 2038), so the paper carries ONE window end for every schedule: build years through 2038.
# The per-schedule expected-loss minimizers (09-09) stay in the SI. The registered 2035 window
# remains the basis of KB1/KB2 and of the w2035 rows of u51/u52.
W_COMMON = 2038
W_VOI = {ab: W_COMMON for ab in SCHEDULES}   # dict form kept: the u51/u52 loop and w43 index by schedule
print("common demonstration-window end (all schedules, build years through):", W_COMMON)

'''
m = BLOCK_RE.search(s)
if m:
    start = m.start()
    s = BLOCK_RE.sub("", s)
    s = s[:start] + NEW_BLOCK + s[start:]
assert s.count("W_COMMON = 2038") == 1


def sub(old, new, required=True):
    global s
    if old in s:
        assert s.count(old) == 1, old[:60]
        s = s.replace(old, new)
    elif required:
        assert new in s, ("neither old nor new present", old[:60])


sub('                for wname, wend_ in [("w2035", W_PRIMARY), ("w2033", W_SENS), ("wvoi", W_VOI)]:\n'
    '                    wend = wend_[ab] if isinstance(wend_, dict) else wend_   # wvoi: per schedule\n',
    '                for wname, wend_ in [("w2035", W_PRIMARY), ("w2033", W_SENS), ("w2038", W_VOI)]:\n'
    '                    wend = wend_[ab] if isinstance(wend_, dict) else wend_   # w2038: the common year (dict form)\n')

# ---- w38 (Fig 6a) ----
sub('    lo_, hi_ = W_VOI_RANGE[ab]\n'
    '    ax.axvspan(min(lo_, hi_) + 0.5, max(lo_, hi_) + 0.5, color="k", alpha=0.06, lw=0)\n'
    '    ax.axvline(W_VOI[ab] + 0.5, color="k", lw=0.8, ls="--")\n',
    '    ax.axvline(W_COMMON + 0.5, color="k", lw=0.8, ls="--")\n')
sub('    Line2D([], [], color="k", lw=0.8, ls="--",\n'
    '           label="last grant year: expected-loss minimizer, per schedule"),\n'
    '    Patch(facecolor="k", alpha=0.06,\n'
    '          label="its range as the price of a cut-off world runs 0.5–2× the median-world bill"),\n'
    ']\n',
    '    Line2D([], [], color="k", lw=0.8, ls="--",\n'
    '           label="demonstration window ends (grants for above-cap need through 2038)"),\n'
    ']\n')

# ---- w39 (Fig 6b) ----
W39_START = "# w39: the credit-feasibility mask alone, display twin (Fig 6b since 2026-09-09)\n"
W39_END = 'ps.savefig(fig, FIGURES / "w39_mask_paper.png")\nplt.show()\n'
NEW_W39 = '''# w39: share of samples covered by the credit, display twin (Fig 6b; Ethan's revisions 2026-09-09/10):
# the 50% statutory maximum only (the existing incentive structure); coverage = 1 - share above the
# cap; one dashed line at the common window end; right-edge labels = share covered in the last build
# year (= the share of worlds that ever become credit-feasible; Table 2 / voi p36).
fig, ax = plt.subplots(figsize=(ps.W2 * 0.62, 3.6))
_ends = {}
for ab in SCHEDULES:
    sub = u51c[(u51c["schedule"] == ab) & (u51c["band"] == "base") & (u51c["cap"] == 0.50)].sort_values("year")
    cov = (1.0 - sub["share_above"].to_numpy()) * 100
    ax.plot(sub["year"], cov, color=ps.SCHED_C[ab], lw=1.4, label=ps.SCHED_SHORT[ab])
    _ends[ab] = (float(sub["year"].iloc[-1]), float(cov[-1]))
# right-edge labels, nudged apart by at least 4 points so they stay legible
_order = sorted(_ends, key=lambda a: _ends[a][1])
_ys = [_ends[a][1] for a in _order]
for i in range(1, len(_ys)):
    _ys[i] = max(_ys[i], _ys[i - 1] + 4.0)
_ys = [y - max(_ys[-1] - 100.0, 0.0) for y in _ys]
for ab, y in zip(_order, _ys):
    x_end, v = _ends[ab]
    ax.annotate(f"{v:.0f}%", xy=(x_end, v), xytext=(x_end + 0.5, y), textcoords="data",
                fontsize=6.5, color=ps.SCHED_C[ab], va="center", ha="left",
                arrowprops=dict(arrowstyle="-", color=ps.SCHED_C[ab], lw=0.4, alpha=0.6, shrinkA=0, shrinkB=1))
ax.axvline(W_COMMON + 0.5, color="k", lw=0.8, ls="--")
ax.text(W_COMMON + 0.8, 98, "demonstration\\\\nwindow ends", fontsize=6, color="k", va="top", ha="left")
ax.set_xlabel("build year")
ax.set_ylabel("share of samples covered by credit (%)")
ax.set_ylim(0, 100)
ax.set_xlim(right=max(v[0] for v in _ends.values()) + 3.0)
ax.xaxis.set_major_locator(MaxNLocator(integer=True))
ax.legend(fontsize=6, frameon=False, ncol=2, loc="upper left", title="schedule", title_fontsize=6)
fig.tight_layout()
ps.savefig(fig, FIGURES / "w39_mask_paper.png")
plt.show()
'''
if W39_START in s:
    i0 = s.index(W39_START)
    i1 = s.index(W39_END, i0) + len(W39_END)
    s = s[:i0] + NEW_W39 + s[i1:]
assert "share of samples covered by credit (%)" in s

# ---- w43 (Fig 6c) ----
sub('GAP_SCHED = list(SCHEDULES)     # every schedule has its own window end (wvoi), eia included\n',
    'GAP_SCHED = list(SCHEDULES)     # common window end 2038, eia included (its builds start in 2038)\n')
sub('    sub = u52c[(u52c["band"] == "base") & (u52c["window"] == "wvoi")\n',
    '    sub = u52c[(u52c["band"] == "base") & (u52c["window"] == "w2038")\n')
OLD_TXT_RE = re.compile(r'ax\.text\(0\.02, 0\.55, "priced through each schedule\'s\\\\nown last grant year: "\n.*\n.*\n'
                        r'        transform=ax\.transAxes, fontsize=5\.5, color=ps\.MUTED, va="top"\)\n')
NEW_TXT = ('ax.text(0.02, 0.55, f"priced through the common last grant year, {W_COMMON}",\n'
           '        transform=ax.transAxes, fontsize=5.5, color=ps.MUTED, va="top")\n')
if OLD_TXT_RE.search(s):
    s = OLD_TXT_RE.sub(NEW_TXT, s, count=1)
assert "priced through the common last grant year" in s
assert "W_VOI_RANGE" not in s and '"wvoi"' not in s, "stale per-schedule window code remains"
p.write_text(s, encoding="utf-8")
print(f"patched _build_notebook_v2.py ({n0} -> {len(s)} chars)")
