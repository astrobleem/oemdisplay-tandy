WINDOWS XT - DOS-NATIVE INSTALLATION

Tandy 1000 EX/HX, 8088, normal 640 KB, DOS 3.3+, Windows 3.0 real mode.
The driver, shell, helpers, wheel input, grabber, original fonts and artwork
are supplied.
You supply your Windows 3.0 installation or original Setup disks.

RUN ON THE DOS COMPUTER
Put WINXT.EXE anywhere on the DOS computer. Exit Windows completely.
To update an existing English Windows 3.0 installation at C:\WINDOWS:

  WINXT UPDATE C:\WINDOWS

It reads Windows Setup metadata and its loader automatically, stages the complete
installer and starts SETUPXT. No Python, modern PC, compiler, conversion or
manual file collection is needed.

For new Windows, insert the first original English Windows 3.0 Setup disk:
  WINXT FRESH A:\

It gathers files from each disk, asking for the next disk until complete.
A complete existing Windows Setup folder also works:
  WINXT FRESH C:\WIN30SRC

Expanded files and original mode-A SZDD files are read directly. The automatic
media cache and prepared source stay on this DOS computer. Allow about 20 MB
for fresh source, installation and temporary files. Windows is installed in C:\WINDOWS.

Fresh Windows Setup: Enter at Welcome and directory. At System Information
select Computer, then the FIRST Tandy 1000 EX/HX (WindowsXT) entry. Confirm
HPXY 640x256, PC/XT keyboard and COM1 wheel mouse. Select No Changes for DOS
configuration. Setup and the finisher continue automatically. Update preserves
unrelated INI entries and shell customization. No manual INI edits are needed.

Start later sessions from plain DOS: C:\STARTXT.
Repair from plain DOS: C:\FIXXT. C:\FIXXT /VERIFY adds full file comparison.
If interrupted, rerun C:\SETUPXT for the existing recovery/resume path.

WINXT.ZIP is the same kit for a DOS ZIP utility: extract on the target computer
and use PREPXR UPDATE C:\WINDOWS or PREPXR FRESH A:\ in that folder.
The complete WINXT.EXE download needs no extraction utility.

USING XR1
The 640x256 logical desktop is viewed through 320x200 in sixteen colours.
XYCTL starts in Software mode. Its menu or Ctrl+Alt+H enables Hardware.
Ctrl+Alt+arrows pan; Ctrl+Alt+Home returns home. WXTWHL supports scrolling in
ordinary Windows controls. The mouse uses COM1/IRQ4, 1200 baud, 7N1.
Windows 3.1 is unsupported.

Minesweeper is separate and is not added by this installer:
https://github.com/astrobleem/oemdisplay-tandy/releases/download/v0.1.0-rc.8/WINMINE30.ZIP

The display and keyboard drivers, fonts and artwork are unchanged. Native results
are in docs/QUAL/DOSINST/RC8.JSN at the source commit in RELEASE.JSON.
No new physical hardware test is claimed. See NOTICE.TXT, OWATCOM.TXT and
individual font/artwork/wheel notices. The supplied CGA grabber is included;
a Windows/DOS installation, disk images, ROMs and proprietary tools are not.
