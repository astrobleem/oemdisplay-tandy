# Windows XT floppy images

The normal download is **WINXT720.IMG**, a standard 720 KB FAT12 data disk
for a compatible GoTek, emulator or double-density floppy drive. The image
inside **WINXT720.ZIP** is identical. It is not bootable and contains no DOS
or Windows installation. Boot your own DOS system first.

## Install with no Python

1. Back up a working Windows 3.0 real-mode installation. The simple path uses
   `C:\WINDOWS` and creates a fresh `C:\WINXT` on the hard disk/CF.
2. Select `WINXT720.IMG` in your GoTek/emulator. At a plain DOS prompt,
   outside Windows, run `A:`, `CD \`, then `INSTALL`.
3. The DOS `PREPXT` helper reads your Windows root and SYSTEM directory for
   the exact supported files. If any are missing, it lists them and stops.
   Copy the files from your own English Windows 3.0 media into a directory,
   then run `INSTALL D:\WIN30SRC` (use your actual path). Up to four media
   directories are accepted; original SZDD compressed files are supported.
   A single-floppy machine can copy its media to hard disk first, then switch
   back to the WINXT image. No Internet, Python or compiler runs on the Tandy.
4. After validation, confirm preparation. The helper creates a new
   `C:\WINXT`, gathers only matching support files, privately creates the
   text-mode font and byte-verifies the staged runtime. It refuses an existing
   destination and never changes Windows files or boot configuration.
5. Run `C:`, `CD \WINXT`, `INSTALL`. In Windows Setup choose Display ->
   Other display, enter `C:\WINXT`, choose your mode and Complete Changes.
   If Setup offers CONFIG.SYS changes, choose option 3 (make no changes).
6. Optional desktop: `C:\WINXT\TSSETUP`. Start Windows through
   `C:\WINXT\WINXT`, retaining reservation/recovery guards.

See the on-disk README and [the existing installation and rollback guide](../../distributions/WINXT/README.TXT).
Preparation alone does not select a display or start Windows. The original
installer owns numbered backups and Windows Setup. Never install directly
from the floppy: the complete working source/backups belong on hard disk/CF.

The public disk deliberately excludes eight Microsoft support files and the
privately derived TXTSYS.FON. It reuses your matching files. Do not redistribute
the completed own-media folder or private image. This adds no license grant for
Microsoft/DDK code, operating-system media, fonts or toolchains.

## Hardware and image format

- Exactly 737,280 bytes; FAT12; 80 cylinders, 2 heads, 9 sectors per track,
  512-byte sectors; 1 KB clusters, two FATs and 112 root entries.
- Normal 720 KB double-density data rate. No 1.44 MB controller, custom
  track geometry, slower-RPM trick or DOS geometry TSR is required.
- FlashFloppy: put the IMG on USB, select it, then access the emulated floppy.
  Other firmware may have different filename/selection conventions.
- DOSBox-X: `IMGMOUNT A WINXT720.IMG -T FLOPPY`. Other emulators must select
  an appropriate 720 KB floppy/controller configuration.
- Real floppy: raw-write the image to supported double-density media. Copying
  the IMG as an ordinary file does not produce a usable disk.
- Keep the image write-protected when practical. The helper writes to CF/hard
  disk. A physical 360 KB-only drive cannot read this 720 KB disk; this full
  six-mode desktop kit does not fit one 360 KB disk. Use CF transfer instead.

Physical GoTek/controller qualification remains separate from emulator tests.
TR5 remains the current default; TRIAL7 and other experimental apps stay separate.
The hardware-text mode retains its existing known character damage.

## GitHub Actions

The [Build Windows XT disks workflow](https://github.com/astrobleem/oemdisplay-tandy/actions/workflows/release.yml)
runs on pull requests, pushes to main, `v*` tags and a manual Run workflow click.
It builds on a standard GitHub-hosted Ubuntu runner with Python's standard
library, runs format/package tests, verifies every publication file and uploads:

- `WINXT720.IMG`: primary mountable disk
- `WINXT720.ZIP`: the same disk plus installation instructions
- `WXTTOOLS.ZIP`: optional portable host-side reproduction tools/source
- `README.TXT`, `BUILD.JSON`, `SHA256SUMS`: instructions, build details, checksums

The artifact is named `winxt-720k-<commit SHA>` and retained for 30 days.
Download it from the successful run's Artifacts section. Durable, anonymous
release downloads must be attached to a reviewed GitHub Release separately.
This workflow has **contents: read**, does not store checkout credentials and
uses commit-pinned actions. It cannot create tags/releases, publish a release,
enable runners or create credentials. An ordinary merge does not publish a
release. No Windows media or user secrets are needed by GitHub Actions.

This is a reproducible **disk/package build from accepted, pinned binaries**.
It is not a claim that GitHub recompiled the historical MASM/DDK code. The
repository's full legacy source/compiler provenance and licensing are separate;
no toolchain is included in the release. Updating binary pins requires separate
source review, CPU/runtime qualification and acceptance.

## Host reproduction (developers only)

Python 3.8+; no third-party packages:

```
python3 tools/FLASHDISK/TESTFAT.PY
python3 tools/FLASHDISK/TESTPKG.PY
python3 tools/FLASHDISK/MAKEIMG.PY --out /new/public-output
python3 tools/FLASHDISK/TESTPKG.PY --verify /new/public-output
```

Each output must be a new directory. Builds use explicit publication allowlists,
verify runtime/helper SHA256 pins, reject extra or stale files, and fix all ZIP
and FAT metadata. Repeated builds produce byte-identical files. The verifier
checks the complete FAT chain/directory structure plus the exact expected
files and bytes. `SHA256SUMS` covers all published assets except itself.

For a private, complete own-media QA image, optionally use:

```
python3 tools/FLASHDISK/MAKEIMG.PY --windows-files /your/media --out /new/private-output
```

That creates `WXTP720.IMG` and a report explicitly marked **not publishable**.
The public workflow has no media input and its final check rejects private
output. Do not upload your private artifacts. Normal end users use the DOS
helper instead; they do not need this optional host path.

`WXTTOOLS.ZIP` contains the same portable scripts and support-free WINXT source.
After extracting, `python MAKEIMG.PY --out /new/output` rebuilds the public
image. The source-level FAT12 tool also supports 360 KB for separate payloads;
that does not turn this full kit into a single 360 KB release.
