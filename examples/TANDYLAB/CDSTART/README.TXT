CDSTART - APP-LOCAL COMMON-DIALOG LAUNCHER
==========================================
Keep CDSTART.EXE, CDTEST.EXE and the matching COMMDLG.DLL together.
Inside your normally started Windows 3.0 real-mode desktop, choose
Program Manager / File / Run and launch CDSTART.EXE by its full path.
Example: C:\TANDYLAB\EXPER\CDLG\CDSTART.EXE
C: is only an example of the Tandy DOS drive. Use its actual drive.
Use CDSTART, not CDTEST directly from an unrelated current directory.
Do not give CDSTART any command-line switches.

CDSTART resolves its own folder, checks for the private pair, temporarily
enters that folder, launches CDTEST, restores the previous active drive
and affected per-drive directories, and exits. It does not install or
copy anything, edit an INI, change PATH, or start/stop Windows. Keep the
normal guarded display-driver startup procedure already used by Windows.
CDTEST.EXE and COMMDLG.DLL remain their unchanged sealed builds.

If any COMMDLG module is already loaded, CDSTART refuses to launch.
Close the demo or other application using it and retry. A missing EXE
or DLL also produces a small error and leaves directories unchanged.

Start with Open/Cancel. For Save/Read use only a NEW scratch filename.
The initial private folder is the default location; the sealed test app
writes CDTEST.LOG there and may create CDxxxx.TMP during file validation.
Never copy this COMMDLG.DLL into WINDOWS or use it as a system replacement.

IMPORTANT BOUNDARY
Restoration is verified immediately after CDSTART's WinExec returns.
Later CDTEST file dialogs can change the inactive drive's remembered
current directory on Windows 3.0. In the two-drive test, C:\WINDOWS stayed
active, but D: later remembered D:\TANDYLAB\EXPER\CDLG instead of D:\BEFORE.
This happened after launcher exit; the child restored its own active
working directory as its NOCHANGEDIR checks required. The launcher does
not remain resident and cannot promise directory invariance for later
child activity. Use full paths for later file operations if needed.

This corrects a Windows 3.0 loader issue: supplying a full CDTEST path
alone did not make its directory part of static COMMDLG import lookup.
This remains a bounded experimental dialog demo, not a general Windows
3.1 common-dialog replacement. Emulator checks are not physical hardware
qualification, manual input qualification, or cycle-accurate speed claims.
