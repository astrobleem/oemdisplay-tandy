# Windows XT: one support folder, six display choices

All six Setup profiles stage the approved static Windows XT fallback
picture (`WXTSPL01.RLE`); there is no older-picture choice or splash prompt.
Windows Setup retains the stock CGA loader. An existing installation is changed
only when you explicitly run INSTALL/Setup. The guarded launcher enables the
short slow flag wave for qualified Color; other profiles keep static startup.
Recovery preserves your original WIN.COM, even if its picture is old.

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

**Long filename browsing is included in Tandy Start 14.** Open Run > Browse to
see existing VFAT long names on supported fixed local FAT12/FAT16 volumes.
The read-only reader requires DOS 6.22, Win3 real mode and 512-byte sectors;
launches still use the displayed short DOS alias. It does not create long names
or let you type long paths in Run. See [NAMES11.TXT](NAMES11.TXT) for limits
and fallback behavior. The installation directory itself still uses DOS 8.3.
The "no long filenames or spaces" rule in the retained runtime README.TXT
refers to installation paths, not the labels displayed in Browse.

The first-run update preserves the original OEM INF as OEMBASE.INF and
records the actual source path in its disk entry. Real Setup completed at
C:\WINXT and C:\XTALT; the unchanged release reproduced the bad C:\WINDOWS
second prompt. Programs has a Windows XT group with savers, About and bundled
Pinball v2. See [qualification and limits](../../docs/FIRSTRUN.MD).

Five TR5 graphics choices include the tested Clock wide-line optimization.
The sixth is explicitly EXPERIMENTAL hardware text: character and geometry
corruption remain. It is not a stable or TR5-optimized graphics replacement.
The optional TSHELL launcher is automatically used only in qualified graphics
modes; text keeps the original Windows shell. Read TEXTMODE.TXT before opting in.
