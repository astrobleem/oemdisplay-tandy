# Windows XT floppy images

## Public downloads

[Windows XT 0.1.0-rc.3](https://github.com/astrobleem/oemdisplay-tandy/releases/tag/v0.1.0-rc.3) includes the qualified guarded slow-wave default.
Choose [WINXT720.ZIP](https://github.com/astrobleem/oemdisplay-tandy/releases/download/v0.1.0-rc.3/WINXT720.ZIP) for the image and
instructions, [WINXT720.IMG](https://github.com/astrobleem/oemdisplay-tandy/releases/download/v0.1.0-rc.3/WINXT720.IMG) for the raw
disk, or [WXTTOOLS.ZIP](https://github.com/astrobleem/oemdisplay-tandy/releases/download/v0.1.0-rc.3/WXTTOOLS.ZIP) for reproduction
tools. [SHA256SUMS](https://github.com/astrobleem/oemdisplay-tandy/releases/download/v0.1.0-rc.3/SHA256SUMS) and
[BUILD.JSON](https://github.com/astrobleem/oemdisplay-tandy/releases/download/v0.1.0-rc.3/BUILD.JSON) bind asset hashes and format.
The release notes link exact source, installation/rollback evidence and
known limits. Public downloads require no GitHub account.

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

The guarded Color launcher runs the short slow flag wave before Windows
loads; a key skips it. Other display modes keep static startup. The updater
privately uses your exact owned `SYSTEM\WIN.CNF`; wrong/changed inputs refuse
safely. It does not patch installed `WIN.COM` or change display settings.

To disable only the animation, exit Windows and run
`C:\WINXT\WAVEXT RESTORE C:\WINDOWS C:\WINXT`.
Use `APPLY` with the same arguments to re-enable. For full rollback, run the
numbered `C:\WINXT\BACKUP\B001\RESTORE YES` path printed by INSTALL. It disables
the wave first and restores byte-verified original resources. Added helpers
remain inactive. Preserve backups and every sidecar after a refusal.

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
Download it from the successful run's Artifacts section. Version-tag builds
also create a **draft** GitHub Release with the same six verified assets.
Drafts are visible to repository maintainers; public anonymous downloads
become available only after a maintainer explicitly publishes the draft.
The build job has **contents: read**, uses anonymous Git
to check out the exact event commit and stores no checkout credentials. It
materializes only the builder/runtime directories and uses a commit-pinned
artifact-upload action. Anonymous checkout avoids credential-cleanup errors
from the repository's historical orphan `dosfetch` gitlink. Pull requests and
ordinary main pushes never run the release job. An ordinary merge does not
create a release. No Windows media or user secrets are needed by GitHub Actions.

Only the separate draft-release job has **contents: write**. It downloads
the successful build's artifact on a fresh runner, executes no repository or
artifact code, rechecks the public output allowlist, 720 KB geometry and hashes,
and attaches explicit filenames. It requires an existing version tag matching
the exact build commit, such as `v1.2.3` or `v1.2.3-rc.1`. Other `v*` tags still
build artifacts but fail the release version check. Existing releases are
refused, including drafts; tags and assets are never overwritten. A partial
upload failure may leave a draft requiring manual inspection; rerunning refuses
to change that draft. Nothing automatically publishes or promotes a release.

Maintainer paths:

- Push a new version tag at the intended reviewed commit. The tag build
  verifies the package and creates a draft, never a public release.
- To retry a build that failed before draft creation, run `release.yml` on
  that same tag/commit and supply its existing tag as `release_tag`.
  For example: `gh workflow run release.yml --repo astrobleem/oemdisplay-tandy
  --ref v1.2.3-rc.1 -f release_tag=v1.2.3-rc.1` (on one line).
- Leave `release_tag` blank for an ordinary manual artifact-only build.

The workflow must already exist on the default branch to dispatch it. An
existing registered workflow can also be dispatched on a reviewed feature
branch whose exact commit has an existing version tag; this allows testing
the draft job before merging. Maintainers should inspect the draft's six assets
and checksums before separately deciding whether to publish it.

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

## Long filename browsing after shell setup

Tandy Start 14 includes [long filename browsing](../../distributions/WINXT/NAMES11.TXT)
in Run > Browse. Existing VFAT labels are displayed read-only on fixed local
FAT12/FAT16 volumes under DOS 6.22 and Win3 real mode; actions retain short
DOS aliases. Floppies, FAT32 and host-folder mounts do not qualify for raw
long-name reading. The installer and C:\WINXT path still use DOS 8.3 names.

The [0.1.0-rc.2 first-run update](https://github.com/astrobleem/oemdisplay-tandy/releases/tag/v0.1.0-rc.2)
uses matching new media-helper/runtime pins, adds Pinball v2 to the explicit
public allowlist, and retains all TR5 driver and splash identities. The older
rc.1 downloads above remain immutable. See [first-run checks](../../docs/FIRSTRUN.MD).

## Independent startup default

WXTTOOLS.ZIP now includes the [accepted slow flag wave](../../examples/WXTSPL/WAVE/README.MD) and its private own-media builder. Executable bytes are pinned to native qualification. The 720 KB Setup installer remains the static fallback; this promotion does not replace its compiled updater or any installed WIN.COM.
