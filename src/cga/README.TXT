IBM CGA DISPLAY FOR WINDOWS 3.0

Tested in Windows 3.0 real mode on IBM XT/CGA
emulation. Physical IBM CGA/CRTC/monitor qualification remains separate.
Target: IBM CGA RGBI, normal 640 KB, existing Windows 3.0 real mode.
Clone CRTCs, PCjr, Tandy, EGA/VGA and Windows 3.1 are not qualified targets.

Extract the complete packet together. Keep SETUP.EXE, this README.TXT and
the expanded CGA folder adjacent. The packet supplies all driver fonts,
dialog faces, grabber and OEM support. No Python or support-file collection
is needed on the DOS computer. Windows itself must already be installed.
Use root SETUP for these choices; the OEM descriptor alone does not perform
the complete dialog-font registration. DOS 3.3+ is required.

Exit Windows completely to DOS. Use your actual Windows directory:

  SETUP C:\WINDOWS 100

Choose 100 for 160x100 in 16 colors, 320 for 320x200 in four colors
(black/bright cyan/magenta/white), 640 for 640x200 monochrome, or PAN for a
320x200 desktop in 16 colors seen through a movable 160x100 window (same
compact fonts as 100). Continue only after the setup success message. Then
change to Windows and start:

  C:
  CD \WINDOWS
  WIN /R

The four choices are separate display-driver geometries. To change mode,
exit Windows and run SETUP again with the new choice. There is no live
geometry switch. Do not run this IBM-CGA packet on a Tandy installation.

UNDO AND RECOVERY

Keep the packet used for installation and its native SETUP.EXE. Exit Windows:

  SETUP UNDO C:\WINDOWS

UNDO restores the INI settings this installer changed while keeping unrelated
later edits. It removes only files this packet created whose bytes still
match and which the INIs no longer reference. Existing identical files and
changed/referenced files are kept. Mode changes use the same native undo
transaction.

SYSTEM.CG0 and WIN.CG0 are original INI safety copies. CGASET.STA records
changed settings; CGACOPY.STA records this packet's created files. Keep them
until UNDO succeeds. CGADONE.STA marks completed INI undo while file cleanup
is pending; rerun UNDO to finish that packet's cleanup. If the settings record
was interrupted or damaged, SETUP refuses normal undo and keeps the copies.
The explicit fallback is:

  SETUP RESTORE C:\WINDOWS

RESTORE puts the saved INIs back whole, losing INI edits made after setup.
Use it only when that is the intended recovery. A failed payload copy leaves
the configuration unchanged; UNDO can clean the packet's own interrupted
copy work. The program refuses unrelated filename collisions rather than
overwriting them. Keep any reported failure receipt for diagnosis.

160x100 has original five-row proportional System/Helv ASCII fonts,
4x6 fixed/OEM text and a 4x5 Courier strike, with six-row
controls. SETUP prints progress while checking and installing files; allow
several minutes on a 4.77 MHz 8088. Unsupported
extended characters currently show a fallback box. The recorded native
Run/Open/Save/Find and control checks pass in the target emulation. Report
clipping or unreachable controls as failures. The initial VRAM policy
blanks video during access to avoid unsynchronized writes; visible blanking
and performance must be measured on the target. No speedup is promised.
An INI larger than 18,000 bytes is refused before any files are copied.

Component notices are in CGA\NOTICE.TXT and CGA\FONTLIC.TXT.

320x200 uses original 4x6 System/Helv and fixed/OEM faces. 640x200 retains
its XTC System/fixed/OEM selection and adds the XT Pixels 8-row proportional
Helv and existing 8x8 Courier dialog faces. Modes 100/320/640 start CGACTL automatically. At 320/640 it
makes disabled labels readable in the reduced palette, then exits. At 100 it
runs the shared WDESK-based window-access client. Ctrl+Alt+arrows move the window workspace; Home recovers
its origin and End exposes the active frame's bottom/right. It can expose a
visible control group clipped inside a fixed client. It does not change the
Windows display geometry. Native integration, Home/recovery and ordinary DOS exit are recorded.
Use normal File Manager window/MDI maximize and File Open commands for its
directory views on this short screen. The recorded DOS-command return test
is a smoke check; it does not qualify every DOS program or PrintScreen.

PAN starts PANCTL instead of CGACTL; the two never run together. Windows
sees a 320x200 desktop and the screen shows a 160x100 part of it. Ctrl+Alt+
arrows move the view, Ctrl+Alt+Home returns to the top left and
Ctrl+Alt+End shows the bottom
right of the active window. Moving the pointer to the edge of the view and
holding it there scrolls the view; a new window or a control reached with Tab
is brought into view. Drawing outside the view appears when it is scrolled in.
Movement commands are kept while Windows is busy loading or drawing and are
carried out in order afterwards (PANKEY.DLL, installed with PANCTL).

Ctrl+Alt+S (or PANCTL /SETTINGS from Run) opens Panning settings, a window that fits the 160x100 view: step
size, dwell before an edge scroll, follow the active window, and pan at the
screen edge. Apply saves them in WIN.INI under [CGAPan]; Cancel changes
nothing. The step is a multiple of 8 across (down is five eighths of it).
Native emulation results for PAN are in the development record; physical IBM
CGA hardware is unqualified.
