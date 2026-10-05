# Windows XT: one support folder, six display choices

This public source deliberately excludes eight Microsoft Windows 3.0 files
and the derived TXTSYS.FON. INSTALL refuses an incomplete source. Prepare
one complete own-media folder on a modern computer, then copy only that
folder to C:\WINXT. No Python or compiler is needed on the Tandy.

Supply your own pinned English Windows 3.0 support files in one directory:
CGA.GR2, CGALOGO.LGO, CGASYS.FON, CGAFIX.FON, CGAOEM.FON,
EGASYS.FON, EGAFIX.FON and EGAOEM.FON. Expanded files and their compressed
SZDD counterparts are accepted; mismatched or ambiguous inputs are refused.

Run `python3 STAGE.PY --windows-files /your/support/files --out /new/WINXT`.
It verifies all hashes, privately derives TXTSYS.FON from CGASYS/CGAFIX while
preserving the CGASYS module identity, and creates the exact flat 8.3 runtime.
Do not mirror or redistribute the completed package containing Microsoft
support files or the derived font. Existing project/DDK provenance is unchanged;
this update makes no new grant over Microsoft code, media or fonts.

At DOS run C:\WINXT\INSTALL, select Other display and C:\WINXT in Setup.
Optional C:\WINXT\TSSETUP installs the shell. C:\WINXT\WINXT is the one
launcher; it always retains the reservation/recovery guards. Backups remain
inside WINXT\BACKUP. No extra TDISPLAY/TANDY88/TSTART root is created.
See README.TXT for complete installation, switching and verified rollback.

Five TR5 graphics choices include the tested Clock wide-line optimization.
The sixth is explicitly EXPERIMENTAL hardware text: character and geometry
corruption remain. It is not a stable or TR5-optimized graphics replacement.
The optional TSHELL launcher is automatically used only in qualified graphics
modes; text keeps the original Windows shell. Read TEXTMODE.TXT before opting in.
