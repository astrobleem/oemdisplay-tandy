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
- `HOSTUI.PY`, `SETTEST.C`, `XYAPPLY.C` - strict C89 tests, including the
  actual XY Apply glue. `VERIFY.PY` binds native builds and saved UI evidence.

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
  still removes autostart and stops the owner, with the same return codes
  (new: 7 = disabled, nothing
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

## Native results

The helpers were built with the established MSC6 and Open Watcom toolchains
and exercised in Windows 3.0 real mode. Exact identities, source/build pins,
raw snapshots, controls, memory readings, owned cleanup and DOS-return proof
are in [NATIVE.JSN](../../docs/QUAL/PANUI/NATIVE.JSN). This is emulator evidence.

| Fixture | Driver geometry | Result |
|---|---|---|
| DOSBox-X PCjr, 640 KB | 320x400 through 320x200 | UI, keyboard, enable/OFF, singleton, Apply/Cancel, persistence, Home, Calculator and exit passed |
| 86Box IBM XT/Plantronics, 640 KB | 320x400 through 320x200 | UI, singleton, Apply/Cancel, persistence, OFF and exit passed |
| 86Box Tandy 1000 HX/8088, 640 KB | 640x256 through 320x200 | XY controls, Apply/Cancel, driver mode readback, duplicate owner, Home, application focus, persistence and exit passed |

Current builds: XTPAN 17,535 bytes; PANCFG 10,191 bytes; XYCTL 21,160 bytes.
The softpan XTPAN uses the exact existing sync_helper transformation. HOSTUI
passes 318 checks with real strict GCC through the managed host wrapper;
`-x c` selects C for uppercase `.C` files and all warning flags are retained.

PCjr and ColorPlus measured a 12,960-byte helper allocation. ColorPlus returned
it exactly. In PCjr the measured Calculator session retained 704 bytes, and
further helper open/remove cycles did not reduce the final free value.
Tandy XY measured a 30,048-byte warm helper allocation; after Calculator and
owner removal, free memory was 161,632 bytes and remained exactly that after
reopen/removal. These are measured fixture observations, not a global
zero-allocation or physical hardware qualification claim.

The dialog follows the existing viewport after timer work without activating
itself or replacing edits. Windows 3.0 Tab/Enter/Escape are handled explicitly.
A disabled PANCFG notice is also positioned inside the physical viewport.

## Current package integration

Native-qualified helper/source pins have been refreshed. JRPAN and ColorPlus
retain their driver, memory guards, ordinary Setup and support bytes. Current
ZIP assembly is `tools/PANUI/PACKAGE.PY`; the main current-release curator
checks these exact ZIPs and continues to use one expanded WINXT source folder.

The expanded SETUP and C6 finisher catalogs bind the larger XYCTL. New main
package output requires `docs/QUAL/PANUI/PACKAGE.JSN`, including exact packet,
Setup and finisher identities and completed native preparation/startup proof.
All remaining checks passed: fresh 370/370, update 83/83, C6 finisher and
CPSET checks, automatic installed-owner startup through STARTXT, settings
and normal DOS return. The owned VM stopped and the lease was released.
No UI update is published or merged by this local qualification work.
