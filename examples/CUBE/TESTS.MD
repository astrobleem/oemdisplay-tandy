# Cube qualification

This is a local candidate. Current coverage is deliberately narrower than
the renderer's supported dimensions. No physical adapter, composite output,
Windows 3.1 or every-driver qualification is claimed.

The current Cube was compiled with MSC6/LINK4 using `/G0 /Gw /AS /W3 /Oat`.
The candidate Tandy Start uses its existing `/G0 /Gw /AS /W3 /Od` build.
The native DOS installer uses Open Watcom `-bt=dos -0 -ms -os`.
No accepted display, font, mouse, keyboard, sound or core packet was replaced.

## Completed before additional mode coverage

The last fully tested 15,615-byte Cube prototype with SHA-256
`4c09c65813dec046961e7191ba8e3bd15bd9475718b08ae624038f62119cdd90`
passed native rendering and input checks at **160x100x16 RGBI** on an emulated
IBM XT 8088 at 4.77 MHz, 640 KB, DOS 6.22 and Windows 3.0 real mode.
It used the project's accepted fixed CGA100 driver and matching compact fonts.

- Flat, ordered-dither and wireframe scenes were visually inspected from
  actual headless scanout captures, held briefly by developer-only QA.
- Six runs covered keyboard wake, held mouse button/release, movement,
  activation loss, Close and stolen capture. Each drew 13 complete frames.
- Each run read a white edge pixel back from both the memory bitmap and
  the screen after the final copy. All six matched `16777215`.
- The held-button check passed; no wake input reached the QA desktop.
  Timer/capture/bitmap/DC/pen cleanup checks reported no retained resources.
- Native DOS installation, shell backup, undo and reinstall completed and
  returned to DOS. The original installer build in this run preceded only
  the additional source-path length guard; the guarded build needs its
  separate final native receipt.
- The run's final receipt confirms its owned emulator stopped, the lease
  was released and the process inventory was zero. It completed despite
  a temporary disconnect of the execution environment.

The measured complete draw cost in this fixture was about 0.77-0.82 seconds
for filled frames and 0.44-0.50 seconds for wireframe after startup. These
are emulator observations using the Windows tick clock, including GDI and
cooperative scheduling. They are not calibrated physical-machine timings.
Small size and Wire are offered to reduce drawing work.

An earlier 14,479-byte prototype passed the same six cases at CGA640 mono.
That record is historical, not final-binary coverage for that mode.

Host checks pass the complete 512-phase geometry period, sine symmetry,
face winding, lighting range and both normal and reduced-copy bounds. The
existing shell transaction suite passes 163 checks, including Cube choice,
custom path, disabling and write-failure rollback. These are C89 host
checks through the managed GCC launcher, not native display qualification.

## Remaining qualification

Native Cube settings save/preview, the compact shell selector and real idle
launch remain pending. Final-binary monochrome, Tandy color and a larger
virtual desktop/viewport also remain pending. The read-only XY viewport
query is implemented but its new consumer use has not yet been accepted.

Developer-only CUBECTL performs UI/idle acceptance in an owned private
Windows fixture. Its `/Q` route runs render/input QA and exits that private
Windows session so DOS can exercise undo/reinstall. Do not distribute or
install the controller as a consumer application.

## Retained failed attempts

The first reused-disk preparation failed while pyfatfs tried to grow a native
DOS file entry. The wrapper incorrectly launched without a complete config;
that owned process was stopped and its lease released. Preparation now
replaces the entry before writing, and the runner requires a completed
preparation receipt and config before launch. Subsequent fixtures use an
explicit private image and the coordinated shared lease.

A stale build-path attempt was stopped before acceptance and is not counted
as qualification. Transitional blank capture attempts were replaced by a
developer-only frame hold and source/screen readback; no mockups are evidence.
