APP-LOCAL COMMON-DIALOG EXPERIMENT - CORRECTED LAUNCH
====================================================
Keep CDSTART.EXE, CDTEST.EXE and COMMDLG.DLL together here.
In Program Manager / File / Run, use the FULL PATH TO CDSTART.EXE:
  C:\TANDYLAB\EXPER\CDLG\CDSTART.EXE
C: is an example Tandy DOS drive; it may differ from the PC card's D:.

Do not launch CDTEST directly by full path from Program Manager. On this
Windows 3.0 setup, its static DLL search uses the current directory and
may fail to find COMMDLG even though the file sits beside CDTEST.
CDSTART temporarily selects its own folder, launches the unchanged demo,
then immediately restores the caller's original drive/directory state. It makes
no INI, PATH, system-directory or startup changes and needs no restart.
If COMMDLG is already loaded, CDSTART refuses: close its apps first.
Missing companions and launch/restore errors are reported, not ignored.
CDSTART then exits; it is not a resident watcher. CDTEST file dialogs can
later change a drive's working directory. In the D:-folder test, D: remained
at the demo folder after those later dialogs. Use full paths for files.

Start with Open and Cancel. For Save/Read round-trip use only a NEW scratch
filename in this folder. CDTEST.LOG is written beside the EXE. File dialogs
can probe writability using temporary CDxxxx.TMP files; cleanup is attempted
but an I/O failure may leave one. The default scratch name is CDROUND.TXT.
Preserve existing files before testing; use a new name if it already exists.

Do not copy the DLL into WINDOWS or overwrite an existing COMMDLG.DLL.
This implements only GetOpenFileName, GetSaveFileName, GetFileTitle and
CommDlgExtendedError within a bounded ASCII DOS 8.3 subset. It is not a
full Windows 3.1/Win32 common-dialog library. Other apps may not load.

The original DLL passed five native automated suites. This pack's launcher
has separate relocated-folder checks; physical mouse/hardware remain
unverified. The sealed CDTEST.EXE and COMMDLG.DLL bytes are unchanged.
SOURCE.ZIP holds the tiny launcher's first-party source, not Windows tools.

Rollback is simply to stop using this private folder; preserve any saved
scratch files before removing it. No Windows configuration was changed.
