XY OVERVIEW / RECOVERY HELPER - EXPERIMENTAL SOURCE

STATUS
This directory is an experimental source and qualification candidate. It does
not change the installed driver, a release package, or the public installer.
The accepted HPXY R1 driver remains unchanged. No guest disks or executables
are included.

PURPOSE
The overview and manual recovery UI are built around the verified R17 XYCTL
helper from the HPXY XR1 source capsule. It uses the existing queried
640x256 logical desktop, 320x200 physical view, and the driver's supported
ESC_XY panning API. The separate src/xtpan/XTPAN.C utility is not modified.
No 2048x2048 desktop, framebuffer thumbnail, CRTC, VRAM, or mouse-ISR access
is introduced.

OVERVIEW AND PAN INPUT
The map is a schematic 1/4-scale outline of queried logical geometry. Its
viewport box tracks the driver-reported origin. The helper accepts only the
supported 640x256 desk and 320x200 view, with X8/Y4 alignment. A click outside
the viewport centers the requested view on that map point; a click inside
preserves the clicked offset while dragging.

Dragging shows a preview. Mouse release sends one aligned set-pan through the
existing ESC_XY driver API. Escape, capture cancellation, focus loss, or a
changed external pan cancels the preview. Mouse-up re-queries the driver and
compares the origin saved at drag start, so an external pan immediately before
release cancels the stale preview without waiting for a timer tick.

The helper tracks the reported viewport origin and stays inset within the
physical view. Ordinary application windows do not follow the viewport unless
the user invokes recovery.

HOME, KEYBOARD, AND MENUS
Pan > Home, the Home button, and Ctrl+Alt+Home request origin 0,0. Existing
Ctrl+Alt+arrow controls pan by X8/Y4. Ctrl+Alt+R invokes recovery. Tab cycles
between the Home and recovery buttons; Enter activates the focused button.
Escape cancels a map drag. Menus retain existing pan, mode, edge, follow, and
repeat commands. These keyboard affordances were not separately qualified by
the Run 08 scripted test.

RECOVERY POLICY
Recovery is manual: use Windows > Bring windows back, its button, or
Ctrl+Alt+R. It first returns the viewport to Home, then considers visible,
captioned top-level windows with nonempty titles. It skips the helper, hidden,
minimized, maximized, child, and untitled windows, shell classes
Progman/Shell_TrayWnd/WorkerW/DDEMLMom, and popup-menu class #32768.

A window is left alone when its titlebar has at least 24 horizontal pixels and
8 vertical pixels inside the logical desk. Otherwise its position is clamped
into the Home view with SetWindowPos without changing size, z-order, or
activation. Recovery guarantees titlebar reachability, not full-window
visibility. Recovered positions are not automatically undone when the helper
closes.

Unsupported or changed driver geometry is reported as unavailable and pan and
recovery controls are disabled. The helper does not claim a map or recovery
succeeded when the driver query fails.

SHUTDOWN AND PERSISTENCE
No settings, handles, or recovery journal are persisted. Normal close and
session-end cleanup asks the driver to select software mode at origin 0,0.
Recovery moves are ordinary window moves and survive normal helper close. A
crash or forced termination may prevent cleanup. XYCTL.LOG retains its
existing 512-record cap.

BUILD
Reproduce the reviewed R17/R19 candidates with the existing Open Watcom C16
1.9 compiler and linker, using the exact source filenames and directives in
this directory. Set WATCOM and the Watcom include/library paths for the local
installation, then run:

  C:\WATCOM\BINNT\WCC.EXE -zW -0 -ms -IC:\WATCOM\H -IC:\WATCOM\H\WIN XYCTL.C
  C:\WATCOM\BINNT\WCC.EXE -zW -0 -ms -od -IC:\WATCOM\H -IC:\WATCOM\H\WIN EDGEQA-OD.C
  C:\WATCOM\BINNT\WLINK.EXE @XYCTL.LNK
  C:\WATCOM\BINNT\WLINK.EXE @EDGEQA-R19.LNK

The -od option and EDGEQA-OD.C filename are required for the tested R19 build.
Build output hashes and compiler/linker logs are recorded in
INTEGRATION-BUILD-RESULT.JSON and BUILD-WATCOM.TXT. Executables, object files,
Windows media, and guest disks are not included.

QUALIFICATION
The integrated XYCTL.C and EDGEQA.C source hashes match the reviewed R17/R19
candidates. A fresh Open Watcom rebuild reproduced the tested executable hashes
with zero warnings and errors. Run 08 passed the focused scripted Win16 map,
pan-cancel, recovery, close, restart, and shutdown assertions with the accepted
HPXY driver profile. See RUN08-STATUS.TXT for accepted assertions and limits.

Run 08 used scripted Win16 window messages, not raw physical mouse or keyboard
input. Its Home query and markers passed, but the Home frame did not provide a
usable visual confirmation. Visual review accepted the settled Drag,
Recovery-Close, and DOS shutdown frames. Unsupported-driver behavior and the
overview on physical Tandy 1000EX hardware remain untested. Run 08 used a
Tandy 1000 HX emulator surrogate and is not hardware qualification.

The separate Run 10 R2 raw-input qualification is not included here and is not
represented as passing. It ended incomplete: the serial drag reached the map
handler, but the test assumed 1:1 mickey-to-cursor scaling. The observed
cursor moved 48x16 pixels for 24x8 mickeys, so the expected-pan assertion
failed. The later helper-close phase timed out before a complete restart and
shutdown result. These observations do not establish a map defect. Raw-input
qualification remains incomplete; keyboard input and physical Tandy 1000EX
hardware were not qualified. The unrelated legacy modal-dialog test was
skipped in focused mode. No installed driver or release package was changed.
