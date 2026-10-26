WINDOWS 3.0 PLACEMENT SERVICE

Windows 3.0 real mode, 8086/8088. WTPLACE.C links as one object with the
caller, like LTWUI.C. Include WINDOWS.H before WTPLACE.H. Functions use
FAR PASCAL and caller-owned FAR pointers; there is no mutable global data,
allocation, enumeration, hook, timer or USER.EXE modification.

WTPlaceInit initializes one caller-owned observation record.
WTPlaceGet captures current state and the real normal rectangle, using
GetWindowRect for normal windows and existing Windows 3.0 USER exports
GETINTERNALWINDOWPOS/SETINTERNALWINDOWPOS (460/461) for saved positions.
WTPlaceAvailable reports whether both exports exist. The service resolves
them through the original KERNEL APIs; no USER files or exports are added.
An unavailable saved-position read leaves a first-observed icon/zoom's
normal rectangle explicitly unknown. It never substitutes an icon rectangle.

WTPlaceSetNormal updates the normal rectangle, preserving iconic/zoomed
and hidden state, activation and stacking. Pinned windows use SW_SHOWNA
or SW_HIDE with the saved-position setter; normal windows use SetWindowPos
with NOACTIVATE/NOZORDER. WTP_MOVE_ONLY preserves the actual normal size.
Every change is read back. An error leaves the latest observed record and
must not be counted as completed recovery. Pinned updates without usable
saved-position exports return UNSUPPORTED, without restoring the window.
HWND/task/instance changes clear remembered state.

The Windows 3.0 SDK Release 1 documents SetWindowPos and EndDeferWindowPos
as void. Newer headers may declare BOOL; those return values must never be
used as success evidence. The service and WDESK verify the resulting state.
Owned icon-title helpers may be created or raised by the saved-position
setter. Group stacking uses unrelated sibling anchors, then is repaired
without activation or geometry changes and read back. No class-number
assumption or hidden-window exclusion is needed.

This is an explicit caller-owned API, not a replacement for Win32
Get/SetWindowPlacement. A caller may retain records for its existing window
table; this module owns no second tracker. WDESK keeps its logical absolute
coordinates separately and supplies the desired physical normal rectangle.
Home, disable, backend switch and shutdown must finish recovery before
discarding the caller's records. A window already minimized is established
from USER's actual saved rectangle. The service owns no duplicated history.

Host mocks test policy and failure handling. A disposable real-mode Windows
3.0 CGA run verified saved-position ABI, canaries, state, active window and
previous sibling for minimized/maximized/hidden updates. The final source
passed a 417.62-second guarded PCjr 320x200 helper/UI/recovery run and a
37.34-second stock CGA 640x200 visible-maximized recovery run. Both exited
normally to DOS. The record measured 20 bytes natively; no heap/global tracker
or desktop bitmap is allocated. See display src/wdesk/EVIDENCE.JSN.
Canonical source is libtandywin/PLACE. The Windows XT WDESK backend is its
first consumer; its source pins and native receipts identify the exact tested
revision. Host checks: python libtandywin/PLACE/TESTS/RUN.PY --out <new-output>.
