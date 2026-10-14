#!/usr/bin/env python3
"""Host test: TEXT80 panned desktop, follow rule with cell-aligned pans.

  python3 src/text80/T80PANT.PY [--json <out>]

The unchanged XTPAN.EXE helper computes the exact viewport top that shows
a newly activated window (FollowTop, src/xtpan/XTPAN.C, copied below line
for line) and asks the driver for it (escape 5850h). The text driver can
only show whole text rows, so T80TALL's t80_panset rounds: a move down
rounds up to a multiple of 8, a move up rounds down. This test runs both
rules together over every window position and height on the 400-row
desktop and every starting top, and requires:

  1. every resulting top is a multiple of 8 within 0..200;
  2. the review regression: a 190-row window at rows 30..220 seen from
     top 0 gets top 20 from FollowTop (as on XTPAN) and top 24 from the
     driver; rows 30..219 are all shown;
  3. every window at most 193 rows tall ends wholly visible, from every
     starting top (8-row cells cost up to 7 rows of the 200-row view);
  4. windows 194..200 rows tall: the positions where 7 rows or fewer are
     cut are counted and reported (a documented limit, not a failure);
  5. negative controls: drivers that round to the nearest row, or always
     down, or always up, must fail check 2 or 3.
"""
import argparse
import json
import sys

VIEW, LOGICAL = 200, 400


def follow_top(top, view, logical, wtop, wbot):          # XTPAN.C FollowTop
    t = top
    if wbot - wtop > view:
        t = wtop
    elif wbot > t + view:
        t = wbot - view
    elif wtop < t:
        t = wtop
    if t > logical - view:
        t = logical - view
    if t < 0:
        t = 0
    return t


def panset(cur, want):                                   # T80TALL t80_panset
    want = max(0, min(want, LOGICAL - VIEW))
    if want > cur:
        want += 7
    return want & ~7


BROKEN = {"nearest": lambda cur, w: (max(0, min(w, LOGICAL - VIEW)) + 4) & ~7,
          "always-down": lambda cur, w: max(0, min(w, LOGICAL - VIEW)) & ~7,
          "always-up": lambda cur, w: min((max(0, min(w, LOGICAL - VIEW)) + 7) & ~7, LOGICAL - VIEW)}


def helper_step(cur, wtop, wbot, driver):
    """XTPAN Follow(): no move when the window is already wholly shown."""
    if wtop >= cur and wbot <= cur + VIEW:
        return cur
    return driver(cur, follow_top(cur, VIEW, LOGICAL, wtop, wbot))


def run(driver):
    bad_range, unseen, cut = 0, [], {}
    for h in range(1, VIEW + 1):
        for wtop in range(0, LOGICAL - h + 1):
            wbot = wtop + h
            for cur in range(0, LOGICAL - VIEW + 1, 8):
                t = helper_step(cur, wtop, wbot, driver)
                if t % 8 or not 0 <= t <= LOGICAL - VIEW:
                    bad_range += 1
                shown = wtop >= t and wbot <= t + VIEW
                if not shown:
                    if h <= VIEW - 7:
                        unseen.append((h, wtop, cur, t))
                    else:
                        cut[h] = cut.get(h, 0) + 1
    regression = helper_step(0, 30, 220, driver)
    return {"bad_range": bad_range, "unseen_193": len(unseen), "unseen_examples": unseen[:5],
            "regression_top": regression, "regression_shown": 30 >= regression and 220 <= regression + VIEW,
            "cut_194_200": cut}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json")
    a = ap.parse_args()
    exact = follow_top(0, VIEW, LOGICAL, 30, 220)
    res = run(panset)
    ok = (exact == 20 and res["bad_range"] == 0 and res["unseen_193"] == 0 and res["regression_top"] == 24
          and res["regression_shown"])
    controls = {}
    for name, fn in BROKEN.items():
        r = run(fn)
        caught = not (r["bad_range"] == 0 and r["unseen_193"] == 0 and r["regression_shown"])
        controls[name] = {"caught": caught, "regression_top": r["regression_top"], "unseen_193": r["unseen_193"]}
        ok = ok and caught
    out = {"follow_top_exact_30_220": exact, "driver": res, "negative_controls": controls,
           "verdict": "PASS" if ok else "FAIL"}
    text = json.dumps(out, indent=1)
    print(text)
    if a.json:
        open(a.json, "w").write(text + "\n")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
