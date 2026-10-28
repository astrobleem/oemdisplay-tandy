# CGA during fresh Windows 3.0 Setup

The integrated CGA packet lets original Windows 3.0 Setup select the project's
fixed **CGA640** driver before its graphical phase starts. It bundles the
matching XTC System/Fixed/OEM fonts, private CGA grabber and startup assets.
It targets an IBM XT/8088 with RGBI CGA and 640 KB. Physical hardware remains
unqualified. Publication requires approval.

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

The Tandy core downloads and historical compact CGA input remain unchanged.
The integrated normal `CGA.ZIP` gains FRESH while keeping its 33 existing
runtime/support members byte-for-byte, including the existing installer,
helpers and OEM descriptor. The original README remains as `CGAOLD.TXT`;
the root README leads with fresh-install instructions.

## Consumer route

Extract the archive on the DOS computer with folders preserved, for example
into `C:\CGAKIT`. Keep the original Windows media separately in `C:\W30SRC`.
Read the included `FRESH.TXT`; then, at plain DOS 3.3 or later, run:

```bat
C:
CD \CGAKIT
FRESH C:\W30SRC
```

`C:\W30SRC` is the **original Windows media directory**, containing Microsoft's
unchanged `SETUP.EXE` and `SETUP.INF`. It is the argument to FRESH. The
**display driver folder** is independently located beside `FRESH.EXE`; this
example prints:

```text
Display driver path: C:\CGAKIT\FRESH640
```

Write down that complete path before starting original Setup. Choose a new
**Windows destination**, normally `C:\WINDOWS`. At **System Information**,
choose **Display**, scroll down to **Other**, enter **`C:\CGAKIT\FRESH640`**,
select **Windows XT IBM CGA 640x200 mono**, then **No Changes** to accept the
hardware list. Use the disk name to answer subsequent copy prompts:

| Requested disk | Path for this example |
| --- | --- |
| Manufacturer's display-driver disk / **Windows XT CGA fresh Setup** | `C:\CGAKIT\FRESH640` |
| **Microsoft Windows 3.0 Disk #1** or another original Windows disk | `C:\W30SRC` |

Setup can prefill the previous disk's path. Replace it when the requested
disk changes. Extracting the kit elsewhere changes the printed driver path;
changing FRESH's media argument does not. For floppy media, insert the first
original English retail Windows 3.0 disk and use `FRESH A:\` from the same
kit directory. The driver path stays `C:\CGAKIT\FRESH640`; Microsoft disk
requests use the requested original floppy in `A:\`.

`FRESH /CHECK C:\W30SRC` verifies without launching anything. The native
launcher verifies original Setup executable/metadata and all eleven fresh-kit
files, then launches original Microsoft Setup. Choose the appropriate keyboard
and mouse; start the installed Windows from its directory with `WIN /R`.
No Python, modern-host conversion, manual INI changes or separate font
gathering is required. The original operating system and the user's usual
DOS ZIP and transfer tools remain prerequisites. [The consumer guide](CGA.MD)
shows the current extraction layout and the complete procedure.

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

The current catalog selects the integrated archive under its normal `CGA.ZIP`
name and supplies the standalone source as `CGASRC.ZIP`. `tools/CGAFRESH` gates
that selection on completed original-media installation, first normal startup,
normal DOS return and independent final-source review. Historical compact/PAN
validators and all four Tandy core identities retain their original contracts.

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

[The receipts and captures](QUAL/CGAFRESH/README.MD) retain those entry-only
tests unchanged. `FULL.JSN` separately records completion on the same private
DOS 6.22 image: its existing original Setup shell was resumed with `WIN /R`,
the remaining original media files were installed, and Setup reported that
Windows 3.0 was installed. Setup returned to DOS. A separate ordinary `WIN /R`
launch reached Program Manager, then normal Exit Windows returned to DOS.
The seven display-support files remain exact and the normal shell is PROGMAN;
no driver replacement or INI patch was used. All 282 source-media files were
checked unchanged. Optional printer setup, application scanning and document
viewing were skipped; suggested boot-file changes were saved as backups.

This covers the known original-media directory route on the 640 KB IBM XT/CGA
fixture. A full floppy-swapping sequence, other fresh profiles and physical
hardware remain separate coverage. The earlier missing-emulator-path launch
failure is retained; it started no emulator. All actual runs stopped only
their owned emulator, released the shared lease and ended with inventory zero.

Every native run needs the shared nonblocking emulator lease, empty emulator
and port inventory, private configuration/image, owned-process watchdog and
verified stop/release. The initial test stops/releases before the exact-candidate
test starts. Buddy's recorded emulator state was released with no playback or
runner queued; no Buddy playback is performed by this work. Only one reused
80 MB DOS 6.22 fixture is needed for the DOS 3.3+ candidate test. No disk images
belong in the public artifact.
