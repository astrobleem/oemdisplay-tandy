XRSYNC: SYNCHRONOUS XR1 OUTPUT / PR155

640x256 logical desktop, 320x200 sixteen-colour Tandy viewport, Windows 3.0
real mode. The driver presents every Output before returning, including an
abandoned BEGIN marker, using narrow column copies and cursor-aware updates.
The included XRSYNC.DRV is the exact 60,800-byte native-tested candidate:
ae2d06f69ff68e64f099c3e0af79028e40e7dca89bd442de23eb18d36be4dca1

PREPARE ON THE HOST (Python 3)
Extract XRSYNC.ZIP. Point preparation at your existing owned Windows 3.0
folder; it finds and verifies the required support file automatically:

  python PREPARE.PY --windows C:\OWNW30\WINDOWS --out C:\XR155

Use your installed Windows folder's host path in place of C:\OWNW30\WINDOWS.
A flat merged source-media folder is also accepted. Preparation checks all
runtime bytes before creating the new complete OEM display folder. Copy the
whole resulting folder to C:\XR155 in DOS. No manual file gathering is needed.
The Windows support file is supplied locally and is absent from the download.

INSTALL FROM PLAIN DOS
Use a separate backed-up stock-CGA Windows 3.0 installation at C:\WINDOWS,
on a Tandy-compatible system with normal 640K conventional RAM. Exit Windows.
1. Run C:\WINDOWS\SETUP. Choose Display, Other, then C:\XR155.
2. Select "Tandy XR1 640x256 synchronous Output". Let Setup install the display,
   grabber, original XT fonts and artwork. Keep your keyboard/mouse choices.
3. Run C:\XR155\RUNSYNC.BAT from plain DOS. It reserves Tandy video memory
   before starting WIN /R. Do this on each boot; do not start WIN directly.
4. In Windows, use Program Manager File / Run: C:\XR155\XYCTL.EXE.
   XYCTL provides viewport pan, Home and software/hardware presentation.
   Existing compatible Tandy keyboard hotkeys remain available if installed.

This is a separate OEM choice named XRSYNC.DRV. Keep an accepted guarded XR1
installation separate: its STARTXT/FIXXT pins deliberately bind its own driver.
Use the saved installation to roll back, or select stock CGA through DOS Setup.
No manual INI edits, launcher-pin changes or writes to physical media are needed.

QUALIFICATION
165 full-VRAM frame pairs match the current-main baseline across origin,
hardware pan (8,56), far software pan (320,56), visible cursor and diagonal
pan/return. Abandoned-BEGIN rows are immediately visible in direct B800 reads.
All 17 RLE cases pass (1,088,000 independent oracle pixels per driver).
Normal DOS Setup installs this OEM kit. A cold boot through RUNSYNC.BAT
passes the cursor-visible pan probe with 17 more matching full-VRAM frames.
At DOSBox-X fixed 3,000 cycles, cursor-key redraw drops from 4,010-4,064 to
549-604 ms; Calculator median drops from 2,142 to 1,099 ms. These are emulator
workloads, not calibrated hardware speed claims. Native-tested driver alias,
per-call pixels, panning and RLE evidence: docs/RRSYNC.MD and docs/rrsync/ at
the release source commit. Physical hardware was not newly qualified.

SHA256SUMS binds the public assets; RELEASE.JSON binds their source commit,
payload and notices. The prepared output contains your Windows grabber and
stays private. No Windows/DOS media, DDK, compiler or emulator is supplied.
See NOTICE.TXT and the separate original font/artwork notices.
