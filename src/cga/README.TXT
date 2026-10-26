IBM CGA DISPLAY FOR WINDOWS 3.0 - DEVELOPMENT CANDIDATE

This packet is awaiting native Windows and IBM CGA qualification. Do not
mistake host checks or a successful native build for tested usability.
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
(bright cyan/magenta/white), or 640 for 640x200 monochrome. Continue only
after the setup success message. Then change to Windows and start:

  C:
  CD \WINDOWS
  WIN /R

The three choices are separate display-driver geometries. To change mode,
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
extended characters currently show a fallback box. Native dialog fit,
font selection and control hit testing still require acceptance. Report
clipping or unreachable controls as failures. The initial VRAM policy
blanks video during access to avoid unsynchronized writes; visible blanking
and performance must be measured on the target. No speedup is promised.
An INI larger than 18,000 bytes is refused before any files are copied.

Component notices are in CGA\NOTICE.TXT and CGA\FONTLIC.TXT.

320x200 uses original 4x6 System/Helv and fixed/OEM faces. 640x200 retains
its XTC System/fixed/OEM selection and adds the existing XT Pixels 8x8
Helv/Courier dialog faces. Mode100 also loads the shared WDESK-based CGACTL access
client automatically. Ctrl+Alt+arrows move the window workspace; Home recovers
its origin and End exposes the active frame's bottom/right. It can expose a
visible control group clipped inside a fixed client. It does not change the
Windows display geometry. This integration still needs native acceptance.
