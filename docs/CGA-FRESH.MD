# CGA during fresh Windows 3.0 Setup: local candidate

This additive candidate lets original Windows 3.0 Setup select the project's
fixed **CGA640** driver before its graphical phase starts. It bundles the
matching XTC System/Fixed/OEM fonts, private CGA grabber and startup assets.
It targets an IBM XT/8088 with RGBI CGA and 640 KB. Physical hardware remains
unqualified. Publication and current-download selection require approval.

## Adapter priorities

| Adapter | Fresh-install consideration |
| --- | --- |
| Tandy EX/HX | Existing full installer already gathers original media and selects HPXY. Preserve its reservation, preparation and finisher path. |
| IBM CGA | Selected first increment: fixed 640x200 needs no panning owner during Setup; the accepted packet supplies a complete OEM display inventory. |
| Amstrad PC1512 | Best next candidate: existing 640x200x16 OEM driver and dedicated video RAM, with no reservation helper. Needs its own original-media fresh test. |
| ColorPlus | Dedicated video RAM needs no reservation. Qualify a fixed initial profile and dialog reachability before extending the fresh path to the panning desktop. |
| PCjr | Its DOS memory driver must reserve the video page and JRGUARD must check it before graphical Setup. Do not bypass that contract with a generic OEM launch. |

Video II and Yamaha/PC1 remain later adapter-specific work. No new fresh
qualification is claimed for them. ROM-DOS and PicoMEM are outside this task.

The current Tandy full-desktop route and the current CGA download remain
unchanged. This is a separate `CGAFRESH.ZIP` candidate. Its 33 existing runtime
and support members are retained byte-for-byte, including the DOS mode-selection
installer, helpers and original OEM descriptor. The original README is retained
as `CGAOLD.TXT`; the new root README leads with the fresh-install instructions.

## Consumer route

Extract the archive on the DOS computer with folders preserved. Read the
included `FRESH.TXT`; then, at plain DOS 3.3 or later, run:

```bat
C:
CD \CGAKIT
FRESH A:\
```

`A:\` is the first original English retail Windows 3.0 disk. A directory
containing unchanged original Windows media also works: `FRESH C:\W30SRC`.
`FRESH /CHECK C:\W30SRC` verifies without launching anything. No Python,
modern-host conversion, manual INI changes or separate font gathering is
required. The original operating system and the user's usual DOS ZIP and
transfer tools remain prerequisites.

The native launcher verifies the original Setup executable/metadata and all
eleven fresh-kit files, prints the absolute OEM driver path, and launches
original Microsoft Setup. At its hardware screen select **Display**, scroll
down to **Other**, enter the printed `FRESH640` path, select **Windows XT IBM
CGA 640x200 mono**, then accept the hardware list. Give the same path whenever
Setup asks for this display disk; give the original OS media for Microsoft
file requests. Choose an unused Windows directory and the appropriate
keyboard/mouse. Start later sessions with `WIN /R`.

The first increment deliberately offers one fresh display profile. Fresh
160x100/PAN would also need placement/helper startup during Setup; the current
320 OEM descriptor does not express the installed packet's distinct CG2 font
selection. Those modes remain available through the unchanged existing-Windows
`SETUP C:\WINDOWS` after fresh installation. That route also supplies its normal
proportional dialog font registration and disabled-text helper. This candidate
does not claim those post-install settings for the graphical Setup session.

Windows 3.1, modified Setup files and different Setup variants are refused.
The recognized retail Setup inputs are `SETUP.EXE` (202,432 bytes, CRC32
4A674EBD) and `SETUP.INF` (49,046 bytes, CRC32 92333A90). They are read only;
no operating system files are in the delivered archive. The initial path test
uses the four original 1.44 MB floppy images; other media sets need their own
qualification even if their Setup files share these identities.

## Architecture and reproducibility

`FRESH.C` is a small-model 8086 DOS launcher, built with external Open Watcom.
Its kit inventory/CRCs are generated from the exact accepted compact CGA
archive by `FRESHPK.PY`. `FRESH.INF` becomes the separate single-choice
`FRESH640/OEMSETUP.INF`. This keeps Tandy's HPXY preparation/finisher and the
existing CGA installer transaction completely separate from this increment.

```text
python src/cga/FRESHPK.PY build --repo . --watcom C:\WATCOM --out NEW-BUILD
python src/cga/FRESHPK.PY pack --repo . --build NEW-BUILD --out NEW-PACKET
python src/cga/FRESHT.PY --repo . --build NEW-BUILD --packet NEW-PACKET --watcom C:\WATCOM --out NEW-CHECK
```

The producer emits expanded consumer files, `CGAFRESH.ZIP`, the standalone
`CGAFSRC.ZIP` rebuild inputs and `CGAFRESH.JSN`. Output directories must be new.
The source archive includes the original accepted CGA packet as a closed
project input, never Windows, the DDK/compiler or an installed guest tree.
Host checks reject changed base/build inputs and modern/protected executables,
check all accepted members and DOS names, and rebuild the source ZIP identically.
They do not establish native Setup behavior.

## Native evidence scope

The first architecture test begins with no Windows directory on a private
20.4 MB PC-DOS 3.20 disk, uses original Windows 3.0 Setup and the current
packet's OEM descriptor, and reaches a visible graphical Windows Setup dialog.
The generated SYSTEM.INI has `shell=setup.exe`, `display.drv=CGA640.DRV`,
the three XTC fonts and `286grabber=CGAGRAB.GR2`. All seven installed display
support binaries match the accepted packet; stock CGA.DRV is absent. BIOS mode
is 06h. The original Setup inputs remain unchanged. This is fresh graphical
Setup evidence, not a driver replacement in an existing installation, and
does not claim completion of the OS installation.

The exact new launcher and dedicated descriptor passed their separate native
test on DOS 6.22 with no Windows installed: missing-media refusal (exit 3),
changed-kit refusal (exit 4), successful read-only check, original text Setup,
the single OEM choice and a visible original graphical Setup dialog. All
twelve native fresh-kit/launcher files match the final candidate; the seven
installed display-support files match their accepted bytes. The final archive
adds component notices and leads with fresh instructions after native staging; no
executable, descriptor or display-support bytes changed.

[The receipt and captures](QUAL/CGAFRESH/README.MD) pin both runs, the final
candidate, host checks and standalone source rebuild. The scope ends at the
graphical Setup options dialog: complete OS installation and first ordinary
`WIN /R` startup are not claimed. The earlier missing-emulator-path launch
failure is retained; it started no emulator. Both actual runs stopped only
their owned emulator, released the shared lease and ended with inventory zero.

Every native run needs the shared nonblocking emulator lease, empty emulator
and port inventory, private configuration/image, owned-process watchdog and
verified stop/release. The initial test stops/releases before the exact-candidate
test starts. Buddy's recorded emulator state was released with no playback or
runner queued; no Buddy playback is performed by this work. Only one reused
80 MB DOS 6.22 fixture is needed for the DOS 3.3+ candidate test. No disk images
belong in the public artifact.
