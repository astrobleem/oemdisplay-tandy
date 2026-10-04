MATRIX /S COMPONENT FOR TSHELL SCREENSAVER INTEGRATION - 2026-10-04

This is the Matrix component for the optional TSHELL idle screensaver.
TSHELL owns idle timing, global input observation, DOS/modal/audio suppression
and configuration. MATRIX contains no resident idle hook or password lock.
Keep a separate installed on-demand package unchanged.

CURRENT AND HISTORICAL FILES
MATRIX.EXE and SOURCE/MATRIX.C are the current /S-capable candidate.
The repository's MILESTONE.ZIP, earlier MANIFEST.JSN and existing EVIDENCE
files remain historical on-demand evidence. They are not current /S results.
See HISTORY.TXT and TESTS.MD for current results and limits.

FINAL BINARY
MATRIX.EXE: 14,157 bytes, Windows 3.0 real mode, /G0 8086/8088 target.
SHA256 0987936c3b80eb9fc5718f3022996514f6885adbdf83cd05128d01bc19de17c8
Baseline: 70ee3dbdb3721844c1eeadcdcecb200ac9f4b8bf2602c70a9c67712b6609cf77

CONTROLLER CONTRACT
- Launch MATRIX.EXE /S. The module name remains MATRIX.
- Saver-only window class: TandyMatrixSaver. Ordinary class: TandyMatrix.
- /S refuses a previous MATRIX instance or existing ordinary/saver window.
  The controller should also check the module before attempting launch.
- The controller can PostMessage WM_CLOSE to TandyMatrixSaver, never to the
  ordinary TandyMatrix window, when disabling the saver or shutting down.
- Both classes are registered by the first instance.
- The controller must check held input, capture/modal/task state and current
  activity generation before launch, then compare activity generation again
  after WinExec. If it changed during loading, close the saver immediately.
- MATRIX rechecks capture, modal state and the saved foreground owner before
  showing the popup, and checks ownership again immediately before capture.
- The controller supplies the automatic timing. /S is not a Windows 3.1 SCR
  interface; no .SCR registration is assumed.

WAKE INPUT AND RESTORATION
/S responds to a new key, key release, character, button or actual cursor
movement. Unchanged synthetic mouse movement is ignored. It does not call
TranslateMessage, so a waking key does not generate an extra WM_CHAR.
Only a release of an already-held launch key within 250 ms can be ignored;
there is no blanket interval that discards genuine new input.

At wake, drawing stops immediately. The popup retains focus/capture while
it consumes queued input and waits for the waking key/buttons to be released.
Keyboard release uses GetAsyncKeyState's physical high bit, never the low
bit or toggle state. Mouse buttons use processed-message state and MK masks;
unsupported mouse virtual-key polling via GetAsyncKeyState is not used.
The popup then waits one quiet interval. For button gestures it waits at
least the configured Windows double-click interval, swallowing the second
click as well. A held key/button deliberately keeps the popup present until
release, instead of leaking repeat/input into the underlying application.
There is no busy loop: the existing Windows timer and message loop are used.

After an ordinary owned wake, the saved active window and focused child are
restored if still valid. Capture is released only when still owned. Drawing
never resumes after wake. If another window/task takes activation or capture,
MATRIX closes without stealing them back. Forced ownership loss, cancellation
or shutdown cannot promise swallowing the remainder of a held gesture.
WM_QUERYENDSESSION stops drawing/drain and closes immediately; either value
of WM_ENDSESSION also safely dismisses /S, including a cancelled shutdown.

The graphics renderer and exact five-name fast-path whitelist are unchanged.
It writes only verified graphics layouts and restores the driver's current
canonical shadow, never a stale desktop snapshot. BIOS mode/page are guarded.
Current trial aliases (BR160/TR33216/TR33204/TR36404/TR26402) are intentionally
not whitelisted and use the ordinary clipped GDI fallback instead.
This component requires no display-driver or reservation-helper change.

No-argument on-demand operation remains immediate-dismiss and retains its
old movement threshold. Only /S adds the release-drain behavior.

VERIFICATION
- Warning-free C6 /G0 /Gw /AS /W3 /Ox build; byte-identical second rebuild.
- Final binary completed fifteen native /A cases in each of five modes:
  160x200x16, 320x200x16, 320x200x4, 640x200x4 and 640x200x2.
- All 75 restoration/control cases returned correct activation and released
  capture. Canonical TNDY6402 uses exact visible-byte comparison; four trial
  aliases use a GDI sample grid (every eighth pixel), not a full-pixel proof.
- Tests include key/char/system-key release, one-pixel mouse motion, unchanged
  synthetic motion, held button and second click, close, deactivation, cancel,
  both shutdown/cancelled-shutdown paths, background repaint and overlap.
- A separate native test confirmed an existing ordinary Matrix remains
  alive/active while a second /S launch is refused.
- Live capture theft was tested in all five modes. Matrix dismissed without
  releasing the other window's capture; that test owner released it itself.
- Five ordinary 60-update /T runs completed, preserving the on-demand route.
- Two held-button checks per mode passed. These and /A input cases use native
  Windows messages; they are not physical mouse/hardware claims.
- The real cloud desktop keyboard test held 'a' for two seconds over an EDIT
  control. Its text stayed UNCHANGED; focus and activation returned correctly,
  and capture was released. That test used build03; final build05 additionally guards live capture
  loss and includes Ctrl-Break in keyboard release checks. The ordinary
  letter-key drain and focus-restoration logic are unchanged; this earlier
  keyboard observation is not represented as a final-build hardware test.
- CUA mouse clicks were not delivered reliably to this DOSBox GUI; no manual
  mouse pass is claimed here. Controller integration owns additional tests.
- 30,000 host ticks and 262,144 packed-pixel checks passed with sanitizers.
- Scoped 8088 control-flow audit checked 4,066 instructions with no later-CPU
  suspects. Imports and unresolved indirect continuations are excluded.
- New /S behavior has not been tested on physical Tandy hardware. Earlier
  acceptance of the on-demand variant does not qualify /S or the new idle
  integration.

BUILD AND REPRODUCE
python3 SOURCE/BUILD.PY --repo <owned-toolchain> --dosbox <dosbox-x> --out <new>
python3 SOURCE/RUNHOST.PY runs portable rendering checks with GCC and sanitizers.
SOURCE/RUNLAB.PY clones an owned installed guest. --mode A exercises /S QA;
--mode T exercises ordinary animation. --standard-shell changes only the
new clone to Program Manager and clears test auto-run entries, avoiding
interference from another test shell. It never changes the source fixture
or display selection. Use a fresh output path and normal 640KB real mode.
TESTSRC/MXGUARD is an optional owned test application, not a required runtime.
Its /D mode runs the ordinary-instance/duplicate-saver refusal check.
