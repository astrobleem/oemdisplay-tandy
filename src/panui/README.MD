# Shared panning settings (src/panui)

One "Panning settings" window for the two existing panning helpers. It
exposes only what the detected backend supports. It is not a new panning
engine: each helper keeps its own timer and pan code, and the window adds no
timer, hook or second process. "Hybrid" here means selectable approaches
under one interface; only the two existing framebuffer helpers are covered.

## Files

- `PANSET.H/C` - pure C89 model: capabilities, defaults, validation,
  WIN.INI load/save through an injected store, the Apply/Cancel/Home model,
  and the command-line and singleton routing tables. No Windows calls.
- `PANDLG.H/C` - the window, built in code from STATIC, BUTTON and EDIT
  children (no resources, no Windows 3.1 controls, no CPL interface).
  `PanDlgOpen(inst, host)` runs inside the owning helper only. A later
  Control Panel wrapper must route like `PANCFG SETTINGS` does: find the
  owner window and post `PS_MSG_VERT` or `PS_MSG_XY` to it.
- `HOSTUI.PY`, `SETTEST.C` - host tests (below).

## Backends and settings

Settings are not merged by name.

| Backend | Detected by | Settings shown |
|---|---|---|
| XTPAN (vertical software pan) | escape 0x5850 | Step (rows), Edge band width (rows), Dwell before pan (ms), Follow any newly activated window |
| XYCTL (HPXY) | escape 0x5860, 640x256 / 320x200 geometry | Pan at screen edge, edge repeat 100/200/500 ms, Follow dialog boxes only, Software/Hardware |

- XTPAN keeps its `[XTPan]` keys and defaults (Step 50, Dwell 400, Edge 3,
  FollowActive 1). Only those four keys are ever written; never Enabled,
  KeyMods, KeyDown/KeyUp/KeyTop, LogKeys or LogFile. No 8/4 alignment is
  imposed on the vertical helper.
- XYCTL persists to a new `[XYPan]` section: EdgeOn (0), RepeatMs (100),
  FollowDialogs (0). Missing keys give today's behavior.
- The Software/Hardware mode is session only: it is applied on Apply and
  never saved, and XYCTL still starts and stops in software. Mode 2 (fault
  injection) does not exist in the UI or validator. Hardware is offered only
  when the DISPLAY stats export (ordinal 106) can read the real mode back,
  and Apply reports what the driver says it is now running.
- Home, Apply and Cancel: Apply validates, applies to the running helper,
  reads back the result, then saves. Failing any earlier step saves nothing.
  Cancel closes and changes neither the helper nor WIN.INI.

## Invoking

- `PANCFG SETTINGS` (or `/SETTINGS`): posts a registered message to the
  running XTPAN, or to a running XYCTL if there is no XTPAN window. If XTPAN is stopped but enabled it is started with
  `/SETTINGS`; if it is disabled PANCFG says so and starts nothing. It never
  edits `load=` or `Enabled`. `PANCFG` alone still enables and `PANCFG OFF`
  still disables, with the same return codes (new: 7 = disabled, nothing
  started).
- `XTPAN.EXE /SETTINGS` and `XYCTL.EXE /SETTINGS`: a second copy only asks
  the first to open its window and exits. A second plain `XYCTL.EXE` now
  activates the first instead of sending a mode escape (before this it
  reset the running copy to software). XYCTL also has Options > Panning
  settings.
- Repeated invocation activates the one existing window; typed edits are kept.

## Host tests

    python src/panui/HOSTUI.PY            (needs a host `cc`; add --crlf to also require CRLF)
    python src/xtpan/HOSTPAN.PY           (unchanged checks)
    python src/xtpan/HOSTTEST.PY

HOSTUI covers defaults, validation, persistence and exact key sets, capability
gating, Cancel/Apply/Home, mode read-back, the command-line and singleton
tables, source-order checks that PANCFG SETTINGS and the XYCTL/XTPAN second
launch route before touching `load=`, a driver escape or WIN.INI, the
`sync_helper` transformation in `src/softpan/BUILDAPP.PY` against the current
`XTPAN.C`, lint, and (when Open Watcom is installed) a 16-bit compile gate.

## Not done here (needs the real Win16 build and a Tandy/emulator)

Nothing in this directory was built with Microsoft C or run on Windows 3.0.
Native checklist:

1. Build XTPAN.EXE, PANCFG.EXE (softpan `BUILDAPP.PY`/`BLDTEST.BAT`) and
   XYCTL.EXE (`experiments/XYOVERVIEW/BUILD-WATCOM.TXT`) with the pinned
   toolchains; confirm `PanDlgProc` is exported in XTPAN (`XTPAN.DEF`).
2. Window fits a 320x200 viewport for XTPAN and XYCTL, Tab/Enter/Esc work,
   Esc cancels, nothing is clipped at the 11-14 px row pitch.
3. Open from `PANCFG SETTINGS` while XTPAN runs: one window; repeat
   invocations only activate it; with XTPAN stopped and enabled it starts
   with the window; with it disabled nothing starts.
4. XTPAN: change Step/Edge/Dwell/Follow, Apply; behavior changes at once,
   `[XTPan]` has only those four keys; Cancel changes nothing; Home works and
   the window stays in view.
5. XYCTL: second `XYCTL.EXE` does not reset the running mode; Apply of edge,
   repeat and dialog-follow takes effect and persists to `[XYPan]`; choosing
   Hardware shows the mode the driver really reports (including a refusal);
   restart comes up in software.
6. Shutdown, driver-loss and window-recovery paths behave as before; the
   dialog closes with its owner.
7. Memory: XTPAN gains roughly 6 KB of code; rerun the softpan memory
   tests (`MEMTEST`, `RAMTEST.PY`) because the PCjr budget is a qualified
   number.
8. Existing keys: `PANCFG`, `PANCFG OFF`, startup via `load=`, Alt+PgUp/PgDn,
   Alt+F9, edge dwell, follow-active are unchanged.

## Known fallout for the packaging owner

`tools/SPPACK/PUBLIC.JSN` pins the hashes of `src/softpan/BLDTEST.BAT`,
`BUILDAPP.PY`, `PANCFG.C`, `PANCFG.RSP`, `src/xtpan/XTPAN.C`, `XTPAN.DEF` and
`XTPAN.RSP`, and `downloads/experimental/SOFTPAN/RELEASE.JSON` embeds the same
identities. This change alters those files, so `tools/SPPACK/TESTPKG.PY` and
`PACKAGE.PY` (the softpan CI job) fail until the pins and release record are
regenerated after native qualification. They were deliberately not edited
here. `tools/EXPPUB/QUALIFY.JSN` also lists `src/xtpan` files, but no test
enforces it.
