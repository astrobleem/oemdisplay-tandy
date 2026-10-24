WINDOWS XT XR1 - CURRENT OWN-MEDIA INSTALLER

Windows 3.0 real mode on an original Tandy 1000 EX/HX, 640 KB RAM, DOS 3.3+.
XR1 provides a 640x256 logical desktop through a 320x200 sixteen-color view,
Tandy Start, original fonts, keyboard panning, hardware-pan controls and
COM1/IRQ4 serial mouse/wheel input. The required project components are here.
You supply Windows and DOS. The prepared output stays private.

PREPARE ON A MODERN COMPUTER
Use Python 3.8+ with its standard library; no compiler or emulator is needed.
Supply a merged folder from the supported English Windows 3.0 media set.
Expanded files and the original mode-A SZDD compression are accepted.
Different media bytes are refused before output is created; the tool does
not fetch missing files or substitute a different Windows release.

For a new Windows installation:
  python PREPARE.PY --windows-media C:\WIN30SRC --mode fresh --out C:\XR1NEW

For an existing Windows 3.0 installation:
  python PREPARE.PY --windows-media C:\WIN30SRC --mode update --out C:\XR1UPD

Use your actual paths and a new output folder. Update preparation needs only
the matching CGA.GR2, WIN.CNF and original SETUP.INF media inputs; fresh
preparation also gathers the Windows Setup files. The supplied PAYLOAD folder
contains the current shell/helpers, adapted display/keyboard drivers, wheel
driver, fonts and artwork. No old private build folder is needed.

The tool verifies every input and generated output. PREPARE.JSN records the
result beside DOS-CROOT. It generates CNF.PIN, XTTEST.COM and modified Setup
metadata from your own Windows files. These generated files contain Microsoft
bytes; do not redistribute the prepared DOS-CROOT or an assembled Windows tree.

INSTALL OR UPDATE FROM PLAIN DOS
Transfer the contents of the new DOS-CROOT folder to DOS C:\ using your normal storage-transfer procedure.
Preserve DOS boot files and boot configuration; none is supplied here.
Allow about 20 MB free for a fresh Windows source/install and temporary files.
Exit Windows completely and run:
  C:\SETUPXT

Fresh Setup uses C:\WINDOWS. At the hardware screen choose the FIRST Computer
entry, Tandy 1000 EX/HX (WindowsXT). Confirm HPXY 640x256, PC/XT keyboard and
the COM1 wheel mouse. Choose No Changes for DOS configuration. Setup and the
finisher complete automatically. An existing installation uses the update
route and preserves unrelated INI settings and shell customization.

Next starts: C:\STARTXT. Repair from plain DOS: C:\FIXXT.
C:\FIXXT /VERIFY requests full file comparison. If installation stops, retain
its journal/recovery files and read the error; rerunning SETUPXT performs the
existing recovery/resume path. Rerun SETUPXT for its recovery/resume path.

USING XR1
XYCTL starts in Software mode. Its menu enables Hardware presentation.
Ctrl+Alt+H toggles the mode; Ctrl+Alt+arrows pan and Ctrl+Alt+Home returns home.
The helper's Help menu lists its controls. Run MODEXT /XR1 from plain DOS to
restore this profile. Other custom display profiles are separate downloads.
WXTWHL starts once for scrolling in supported ordinary Windows controls.
The mouse driver uses COM1/IRQ4, 1200 baud 7N1, two buttons and an optional
signed wheel nibble. This package is for Windows 3.0 real mode, not 3.1.

Minesweeper is a separate WINMINE30.ZIP download with its own short install
guide and tested About shim; SETUPXT does not install it automatically.

QUALIFICATION AND NOTICES
Read QUALIFY.JSN for exact emulator test scope and remaining limits, and
NOTICE.TXT for authorship, adaptation and component notices. The final package
and new wheel driver have emulator qualification; no new physical run is
claimed. Earlier real-EX panning acceptance has its own separately scoped
record. Large redraws and some apps can still be slow on an original 8088.
