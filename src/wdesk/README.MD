# WDESK window workspace

WDESK moves top-level application windows in an absolute coordinate workspace.
A 2048x2048 workspace allocates no bitmap. The existing helper owns one selected
engine and its existing timer; framebuffer and window movement do not run
together. The shared settings choose one available approach at a time.

The core came from PR198 head `204787446d5d7ee24c2752749f594caeb4803fe1`.
It retains its original 24-byte entries and absolute-coordinate model.
`WDWIN.C` uses the explicit libwintandy placement service in
`libtandywin/PLACE/WTPLACE.C`. Link that source as one object; the library does
not add a window table, timer, hook, DLL, USER export or USER.EXE replacement.
The byte-identical pinned source mirror is src/wdesk/PLACE; SOURCE.JSN records
the canonical library commit. Developer builds use it by default.

## State and recovery

Every tracked window stores its logical normal rectangle. Screen targets are
`logical - origin`, with long intermediate arithmetic and bounded 16-bit values.
Workspace/screen limits are 4096 per edge; stored coordinates clamp to
-16384..16383. Viewport movement clamps to the workspace. WDCORE owns no heap or
static state; the Win16 adapter owns one existing fixed table.

| Case | Policy |
| --- | --- |
| New application windows | Visible, captioned top-level windows of another task are eligible. |
| Child/menu/icon-title/helper windows | Children and captionless windows are not adopted; the menu class is excluded. No assumed icon-title class number. |
| Hidden or newly captionless tracked frame | Retained for recovery while its full identity still matches; moves do not show it. |
| Owned/dialog windows | Absolute targets in owner-first order, including an otherwise unchanged owned target when its owner moves. This works whether USER moves popups with owners or leaves them alone. |
| Minimized/maximized | Pinned during ordinary pans; saved normal rectangle is read through the placement service. Icon and maximized rectangles are never substituted. |
| First seen minimized/maximized | Established from USER's real saved normal rectangle. An unavailable read remains explicitly unknown. |
| Restored window | Next plan moves it to its remembered logical position once. |
| User drag/resize | Adopted from actual position plus origin. |
| Closed/reused HWND | Full task, instance and class identity decides retention; a new object must pass eligibility again. |
| More than 24 eligible windows | Extras are untouched and counted. Panning stops with `WD_E_FULL`; Home remains available. Previously moved windows cannot be evicted by new foreground windows. |

Current recovery uses the placement service's saved-position API. Home keeps
tracked pinned/hidden states and repairs their saved rectangles, rescuing captions:
at least min(width,40) horizontal pixels and the caption height must be reachable.
Owned windows follow the owner's rescue shift before their own caption clamp.
The saved-position ABI/state/focus behavior was verified in a disposable Windows
3.0 guest. The service resolves existing USER460/461 exports dynamically behind
its own API; it does not add exports or replace USER.EXE. A failed saved update
retains recovery ownership. The earlier restore-to-normal prototype was removed
after native testing showed it activated an application.

Every emitted target is checked against USER after the batch. If a deferred
batch fails, individual moves are attempted. Failed moves retain the logical
target and actual last-known coordinate, so retries do not become false user
drags. A negative Home/shutdown result retains recovery ownership and the
helper must stay alive. `WDWinPrepareShutdown` recovers without discarding the
initialized owner if another application cancels Windows shutdown.

There is no crash-time recovery code. Ordinary Home, disable, backend change
and normal shutdown must complete before releasing the backend.

## API and helper integration

```
int WDWinInit(int workspaceW, int workspaceH);
int WDWinInitView(int workspaceW, int workspaceH, int viewW, int viewH);
int WDWinExclude(LPCSTR classname);
int WDWinReconcile(void);
int WDWinPan(int x, int y);
int WDWinPanBy(int dx, int dy);
int WDWinHome(void);
int WDWinPrepareShutdown(void);
int WDWinShutdown(void);
void WDWinViewport(int *x, int *y);
unsigned WDWinDropped(void);
```

The shared settings offer Windows workspace only on a fixed
320x200 or 640x200 reported screen, through explicit Settings invocation.
Existing virtual-framebuffer profiles retain their software/hardware choices:
their reported logical screen is larger than the physical viewport and must
not be mistaken for a fully visible fixed display. UI mode3 is local and never
passed to a driver; mode2 remains rejected fault injection.

XTPAN retains its existing 55ms timer and the exact softpan `sync_helper`
transformation. XYCTL retains its existing 100ms timer. No extra owner class,
timer, hook or export is added. Driver binaries and ABIs are unchanged.

## Developer checks

```
python -B src/wdesk/BUILD.PY --out FRESH_DIR --placement LIB_PLACE_DIR --win30-system WIN30_SYSTEM_DIR
python -B src/wdesk/ADAPTER.PY --out FRESH_DIR --placement LIB_PLACE_DIR
python -B LIB_PLACE_DIR/TESTS/RUN.PY --out FRESH_DIR
```

Host tools use the managed GCC launcher with explicit `-x c`, strict C89 and
warnings as errors. WDCORE has 30,705 checks and three negative controls.
ADAPTER compiles actual WDCORE/WDWIN/WTPLACE against bounded USER mocks;
placement checks compile the actual service separately. Those are host policy
checks, not native evidence.

BUILD also compiles/links an 8086 Win16 stub with Open Watcom and validates its
NE3.00 header/imports against real Windows 3.0 modules. Measured foundation
adapter static state is 1,404 bytes, 24 bytes/window (576-byte table), with no
large-desktop bitmap. Rebuild maps record total code/stack separately; these
figures do not measure native runtime speed or actual free memory.

NATPREP prepares an MSC6 QA client from the existing UITEST observer and actual
helper sources. Test-only direct USER460/461 commands use canaries and log saved
normal rectangles, state, active window and stacking position. They verified the
ABI used by the library candidate in disposable emulated Windows. No physical
register or USER patch is used.

Native acceptance passed on a guarded normal-640KB PCjr fixture with the fixed
320x200 TNDYJR driver: both helper frontends, Apply/Cancel/persistence, singleton
routing, two-dimensional panning, owned modal offsets/Home, first PANCFG OFF,
XY Home/shutdown, activation/application order, minimized restore, maximized to
minimized to maximized restore, continued File Manager use and normal DOS exit.
The regular softpan helper uses the exact sync transformation and MSC6 build;
XYCTL retains its established Watcom toolchain. The run took 417.62 seconds.

A focused stock-CGA 640x200 run passed in 37.34 seconds: the saved normal
rectangle was repaired while Calculator remained maximized, and the rectangle
restored correctly after shutdown. The native placement record was 20 bytes.
All owned processes stopped and each shared lease released. These are emulated
Windows 3.0 results; no physical adapter qualification or USER backport is claimed.
XYCTL was exercised as a window-workspace frontend on PCjr, not as HPXY scanout.

The Windows 3.0 SDK documents SetWindowPos and EndDeferWindowPos as void.
The candidate discards their undefined returns even when newer headers declare
BOOL, then verifies actual positions/state. Host mocks use void declarations to
catch regressions. See EVIDENCE.JSN for identities, exact scope and corrections
to earlier unsuccessful runs. Current package qualification is in
docs/QUAL/WDESK; earlier records remain frozen. Driver bytes are unchanged.
