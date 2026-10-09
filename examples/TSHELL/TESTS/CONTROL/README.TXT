Settings integration tests
==========================

TESTCP.PY compiles the production TSCP.C with a narrow Windows API fixture.
Run with CC pointing to an existing C89 compiler. It verifies all ten
native command routes, Control Panel reuse, open-only behavior, missing
files, launch errors, failed window discovery, busy dialogs, absent menus,
disabled/separator/popup commands, mismatched captions and failed posting.
Keyboard tests cover loaded/missing module, present/absent SetSpeed export,
supported/unsupported query results, graying only Keyboard and direct-command
fallback. Every driver call is asserted to use the read-only argument -1.

TESTMN.PY extracts the production TSHELL popup and deferred dispatch code
and compiles it with MNTEST.C's API fixture. It verifies narrow/wide menu
composition, Settings deferral until Start tracking ends, focus guards,
cancellation cleanup, computed vertical bounds and allocation failures.
These host checks do not claim native menu key or mouse input behavior.

CPREAD.PY requires the owned Windows 3.0 CONTROL.EXE and the already
available host Capstone module. It verifies exact resource menu IDs,
captions, the main window class, and that this binary's complete WinMain
does not read the lpCmdLine stack words. It writes metadata only. Never
include owned Windows files in a source or runtime delivery.

Native qualification still required:
- Build TSHELL using pinned BUILDDEPS with /G0 /Gw /AS.
- At 160 and 640 pixels, open Settings using both keyboard and mouse.
- Open every applet, cancel/close without changing private fixture settings,
  reopen, return to the bar, and check focus and held-key navigation.
- Reuse an open/minimized Control Panel and an already open applet.
- Confirm the screen saver and existing System/clock settings remain usable.
- Test missing CONTROL.EXE in a disposable fixture, and a disabled/missing
  or caption-mismatched native item; the Control Panel fallback stays open.
- Close the secondary bar and use normal/Shift Windows exit.

Only start a guest after the parent grants a bounded emulator allocation.
Acquire the shared lock with an immediate nonblocking busy refusal, stop
only owned guest processes, and release the lease in finally.
