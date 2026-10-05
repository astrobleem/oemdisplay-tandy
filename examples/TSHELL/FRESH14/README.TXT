TSTART14 FRESH-KIT ASSEMBLY

This repository folder contains installer/configuration sources, not all the
runtime applications. Do not copy this sparse folder to a Tandy and expect
TSSETUP.BAT to succeed. Assemble the complete kit first, or use the supplied
complete TSTART14 archive.

The complete kit places these files in C:\WINXT:
TSHELL.EXE, TSINPUT.DLL, SHELLSEL.EXE, RESERVE.COM, MATRIX.EXE, MAZE.EXE,
STARFLD.EXE, TABOUT.EXE, TCHIME.EXE, XPCHIME.EXE, TEXIT.EXE, TSCHECK.EXE,
TSSETUP.BAT, TSTART.BAT, TSREADY.TXT and TSHELL.INI.
RUNTIME.JSON records each exact tested binary identity.

Repository source locations in oemdisplay-tandy:
- examples/TSHELL: current TSHELL and TSINPUT binaries/source
- examples/TSHELL/DOS: SHELLSEL source and runtime
- src/tandysw/RESERVE.ASM: unchanged reservation helper source
- examples/MATRIX/SOURCE: current Matrix source
- examples/MAZE/SAVER10/SOURCE: current Maze saver source
- examples/STARFLD: current Starfield source
- examples/TABOUT: About this Tandy source

Sound sources live in the separate astrobleem/oemsound-tandy repository:
src/win30/CHIME, src/win30/XPCHIME and src/win30/TEXIT. Use the compact TEXIT /go
source published with the shell integration, not an older preview-only binary.
Build the apps with the documented licensed period toolchain; do not bundle
Windows, SDK libraries, compiler binaries or disk images.

To assemble on a build computer, put the twelve exact binaries listed in
RUNTIME.JSON in one input directory, then run:
python3 ASSEMBLE.PY --inputs INPUTDIR --out NEWDIR
The helper checks every hash before copying anything into a new output folder.
It produces NEWDIR/WINXT. It does not install on the build computer.
TSSETUP.BAT itself uses stock DOS commands plus the supplied SHELLSEL and TSCHECK;
no Python, ANSI.SYS, long-name TSR or modern-PC metadata map is needed on DOS.

COPY AND INSTALL ON THE TANDY
Copy the complete WINXT folder to the card root. If it is D: on the build PC,
D:\WINXT becomes C:\WINXT on the Tandy. Avoid a nested WINXT\WINXT folder.
Windows 3.0 and the selected compatible display driver must already be installed
in C:\WINDOWS. Exit Windows and run C:\WINXT\TSSETUP without arguments.
In the combined kit, follow the top-level INSTALL for display Setup, then
run TSSETUP. On success use the common C:\WINXT\WINXT launcher. The active shell/DLL/INI go in C:\WINDOWS;
all companions remain in C:\WINXT. The fresh configuration is self-contained.

TSSETUP refuses existing shell files or its backup names. It preserves
SYSTEM.INI and WIN.INI as BACKUP\SHELL14\SYSTEM.INI and WIN.INI without replacing either
Windows configuration file. An interrupted copy has not selected TSHELL; keep
all backups and resolve the copy error before launching. Reusing this fresh
INI on an existing installation would replace custom settings, so upgrades
should copy only the two current shell/DLL files and preserve configuration.

TSTART recovers any unfinished shell journal, checks the required files,
runs the unchanged RESERVE.COM, selects TSHELL and runs WIN /R. A reservation
failure stops before shell selection. Successful Windows return uses FINISH;
Windows errors use plain RECOVER. The moon screen appears only after verified
restoration and journal cleanup. Application vetoes keep Windows running.
After interruption: C:\WINXT\SHELLSEL RECOVER C:\WINDOWS\SYSTEM.INI
Keep sidecars until recovery succeeds. Never restore stale whole Windows INIs
over new display/keyboard settings. To open the original shell afterward, run C:\WINXT\RESERVE.COM first.
Stop on any failure. Only after successful reservation run C:\WINDOWS\WIN /R.
Never bypass reservation after a reset when using a graphics driver.

The optional TNDYK3 keyboard kit has its own guarded installer. This fresh kit
does not select it. Hold defaults off with the stock keyboard; the Start button
still works. Chime apps use PSG directly and require no sound-driver installer.
See ../README.MD, ../TESTS14.MD and FULLTEST.TXT for behavior and evidence.

TSCHECK is a small read-only 8088 byte comparator. It checks every installed
file and both backups. SHREADY.TAG is created only afterward using a checked
temporary file and rename. Existing markers/partial states are refused.
The generated common WINXT launcher also gates the shell on qualified
graphics modes; experimental text uses the original shell. TSSETUP supports
the default C:\WINDOWS target only. The combined kit adds display assets. Keyboard and wallpaper remain separate
opt-in extras. See distributions/WINXT/README.MD for the main workflow.

This component assembly is only the shell payload. The combined package
provides the main INSTALL and generated WINXT launcher. For a standalone
assembled shell payload with a working graphics driver, TSSETUP followed by
C:\WINXT\TSTART is the direct route. Source/evidence ZIPs are separate from
the compact CF runtime and are not required on the card.
