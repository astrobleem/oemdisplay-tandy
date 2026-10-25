# WDESK - window-moving virtual workspace core

A selectable alternative to the framebuffer panning backends (XTPAN, XYCTL).
It moves top-level application windows relative to the visible screen. A
2048x2048 workspace here is a coordinate range only: nothing the size of that
bitmap is allocated. It must not run at the same time as a panning backend.
This directory is self-contained; no driver, installer, pin or release file
and none of src/panui, XTPAN, XYCTL or PANCFG is touched.

Status: host-tested core and a compile/link-checked Win16 adapter. Nothing
here has run on Windows. Native behavior is unverified until dot's checklist
below is done.

## Files

| File | Role |
| --- | --- |
| WDCORE.H/.C | Pure C89 state and positioning logic. No Windows calls, no heap, no static data. |
| WDWIN.H/.C | Win16 adapter: observes windows, applies moves. Windows 3.0 APIs only. |
| WDTEST.C | Host tests with a mock OS (30,000+ checks), including fault-injection controls. |
| WDSTUB.C/.DEF | Link-check stub, never shipped. wlink does not read the DEF; BUILD.PY writes the equivalent directives. |
| BUILD.PY | Developer script: host tests, negative controls, Win16 compile/link, size, NE and import checks. |

## Model

- Every tracked window stores an absolute logical rectangle (16-bit values,
  long intermediates). Its screen position is always computed as
  `logical - viewport origin`. Deltas are never accumulated, so any number of
  pan cycles returns windows to exactly their original coordinates.
- Limits: workspace 1..4096 per edge and not smaller than the screen; screen
  1..4096; logical coordinates clamp to -16384..16383; sizes to 0..16384;
  viewport clamps to the workspace. Out-of-range input is clamped or rejected
  (`WD_E_RANGE`), never wrapped.
- Capacity is `WD_MAXWIN` = 24 tracked windows. Extra windows are not tracked,
  never moved, and counted in `dropped`. No claim is made about how many
  applications Windows 3.0 in 640 KB can really run.
- Viewport (0,0) is the identity: logical equals screen. Disable and Home
  therefore return to what Windows itself believes.

## Window policy

| Case | Behavior |
| --- | --- |
| Top-level visible windows | Tracked and moved. |
| Child windows (`WS_CHILD`) | Never enumerated or moved; they follow their parent natively. |
| Hidden windows | Not tracked. One shown later is adopted at its current screen position. |
| Shell desktop | Not a top-level child of itself; never enumerated. |
| Our own task's windows | Always excluded (the helper's window, control dialogs). |
| Menu / icon-title classes | Excluded by default (`#32768`, `#32772`). Owner adds more with `WDWinExclude` (for example `XTPan`, `Progman` only if it must stay fixed, `TandyStart`). |
| Owned popups and dialogs | Tracked as separate entries, each with its own logical rectangle, so the owner/dialog offset is preserved by construction. Windows does not move owned windows with their owner, so nothing is ever moved twice. Each hwnd appears at most once in a move batch. |
| Modal dialogs | Same as owned popups. Panning is allowed; Home brings owner and dialog back together. |
| Minimized (icon) | Pinned. The icon is never moved. The last normal rectangle is kept. |
| Maximized | Pinned. Same. |
| Restore | Windows restores to its old screen rectangle. The next plan moves it to `logical - origin` in one move. A window first seen minimized or maximized is adopted on restore using the viewport origin at first sight. |
| User move or resize | Detected at reconcile by comparing the real position with the last commanded one. The new logical position is `actual + origin`. |
| Handle reuse | An entry is identified by hwnd plus task, instance and class hash. Any difference makes it a new window with no inherited state. |

Windows 3.0 has no `GetWindowPlacement`/`SetWindowPlacement` (a real 3.00
USER.EXE does not export them), so restore rectangles of minimized or
maximized windows cannot be edited. Pin-and-replace above is the substitute.

## Home, recovery, disable

`WDHome` sets the viewport to (0,0). Every window with a stored normal
rectangle (including minimized/maximized ones, for their later restore) is
shifted by the minimum amount so that its caption strip lies fully inside the
screen vertically and at least `min(width, 40)` pixels of it are visible
horizontally. Owned windows first take their owner's total shift (resolved in
dependency order, any table order), then get their own check. `WDShutdown`
is Home, the final moves, then forgetting every window. After that, a
window that was minimized or maximized restores to whatever rectangle Windows
itself remembers (Windows 3.0 has no `SetWindowPlacement`), which can lie
off-screen if it was minimized while panned away; Home first rescues stored
rectangles, shutdown cannot rescue what it no longer tracks. Call it on helper exit
and on backend switch-off; windows are then reachable and Windows' own
coordinates are authoritative again. If the helper crashes, nothing can run
this; press the Home key or restart the helper before the next session.

## Activation, z-order, redraw

All moves use `SWP_NOZORDER | SWP_NOACTIVATE | SWP_NOSIZE`, batched in one
`BeginDeferWindowPos`/`DeferWindowPos`/`EndDeferWindowPos` (falling back to
individual `SetWindowPos` if the batch fails). No focus, activation or z-order
call is ever made. A pan that changes nothing makes no Windows call at all.
Windows repaints moved windows itself; smoothness is unmeasured.

## Observation contract (no hooks, no timer, no window class)

The module observes nothing in the background. The single owner must call
`WDWinPan`, `WDWinPanBy`, `WDWinHome`, `WDWinShutdown` or `WDWinReconcile`;
each moving call reconciles first. Windows opened, closed, moved or resized
between calls are noticed only then. The existing helper already has a 55 ms
timer (XTPAN.C `SetTimer(hMain,1,55,NULL)`); reconcile on pan, Home and
shutdown needs no extra timer. Calling `WDWinReconcile` from that timer is an
optional later choice for dot, and is not added here.

## Ownership and lifecycle

- One owner (the existing single-instance helper) initializes it, drives it
  and shuts it down. The module has no global registration and runs no code on
  its own.
- Init: `WDWinInit(2048, 2048)` once the backend is selected, then
  `WDWinExclude` for the helper and shell classes.
- Run: `WDWinPan`/`WDWinPanBy`/`WDWinHome` from the owner's key, mouse-edge or
  settings events.
- Exit/disable/backend change: `WDWinShutdown()` before releasing the
  backend. It is safe if never initialized, and if called twice.
- Never run together with framebuffer panning; the owner picks one backend.

## Minimal integration API

```
int  WDWinInit(int wsw, int wsh);
int  WDWinExclude(LPCSTR classname);
int  WDWinPan(int x, int y);        /* absolute origin; returns windows moved */
int  WDWinPanBy(int dx, int dy);
int  WDWinHome(void);
void WDWinShutdown(void);
void WDWinViewport(int *x, int *y);
unsigned WDWinDropped(void);
int  WDWinReconcile(void);
```

Files dot touches later: add WDCORE.C and WDWIN.C to the owner's build (small
model, `WDWIN.H` defines `WINVER 0x0300`); route the owner's pan/Home events
to the calls above; call `WDWinShutdown` on exit and on backend change; add
the backend choice to the shared settings model. Nothing else: no new window
class, no EXPORTS entry, no timer, no hook. Open Watcom flags that were
verified: `wcc -bt=windows -ms -0 -os -zq -w4 -we -zw`.

## Measured size (host tools, not native)

From BUILD.PY (Open Watcom 16-bit, small model, 8086 code):

| Item | Bytes |
| --- | --- |
| Per tracked window (`sizeof(WDENT)`) | 24 |
| Window table (24 windows) | 576 |
| Core state `sizeof(WD)` | 596 |
| WDCORE code (`_TEXT`) | 2,268 |
| WDWIN code (`_TEXT`) | 1,245 |
| Adapter static data | 1,400 (state 596, snapshot 640, moves 144, exclusions 16) |
| `WDHome` stack locals | about 120 (three 24-entry arrays) plus a few words |

The linked check stub (19,122 bytes with the Watcom stub; `_TEXT` 0x1110) is
larger because it includes the C startup and runtime. Per-pan cost on a
4.77 MHz 8088 is unmeasured: reconcile matches each observed window against
a 24-entry table (quadratic) and calls several USER functions per window.
Measure it natively before any claim about speed or smoothness.

## Header verification

Declarations were checked three ways: Watcom `h\win\windows.h` with
`WINVER 0x0300` (Get/SetWindowPlacement then undeclared), the project's own
locked `DDK/286/INC/WINDOWS.H` + `WINDOWSX.H` from commit 96ce697 (every
identifier used is present, and `WDWIN.C` compiles with zero warnings against
it; this one was a manual compile, not part of BUILD.PY), and the import names
of the linked stub against real 3.00 USER/KERNEL exports. All compiler flags
verified are Open Watcom's; the owner's MSC6 build is untested here.

## Checks

```
python -B src/wdesk/BUILD.PY --out FRESH_DIR --win30-system PATH_TO_WIN30_SYSTEM
```

Host checks (strict C89 through the managed GCC launcher, test suite, three
negative controls) and Win16 compile/link (Open Watcom, NE header, imports
checked against a real Windows 3.00 USER/KERNEL) are separate from native
runtime evidence, which has not been collected. The negative controls
(`WD_FAULT_OWNER`, `WD_FAULT_REUSE`, `WD_FAULT_PIN`) rebuild the core with a
deliberately broken rule and require the suite to fail.

## Native checklist (for dot)

Stock Windows 3.0 real mode, Notepad, Calculator, Clock and File Manager.

1. Start helper in WDESK mode; Notepad and Calculator at their normal places.
2. Pan right and down; both move together, spacing unchanged; focus and the
   active title bar do not change; z-order unchanged.
3. Pan back to the origin; both are at their exact original places.
4. In Notepad, File Open (modal dialog) while panned: dialog and Notepad keep
   their offset when panning; Home brings both into view; cancel works.
5. Minimize Notepad, pan, restore: it returns to its logical place, once.
6. Maximize Calculator-sized or File Manager, pan: it stays full screen; restore
   returns it to its logical place.
7. Open a new window while panned: it appears where you see it and then pans
   consistently. Close one and open another: no ghost position.
8. Drag a window while panned, pan back and forth: it keeps its new place.
9. Pan so a window is off-screen, press Home: it is reachable.
10. Exit the helper with windows panned away: all windows are reachable.
11. Open menus and the Task List: not moved; icon titles not tracked (check
    that `#32772` is really the icon title class on 3.0).
12. A repeated pan with nothing to move: no flicker or repaint.
13. Record memory (Help, About) before and after on a 640 KB machine, and
    time a pan with 3, 8 and 24 windows. These are the only numbers that may
    be quoted.
