Current unified-panning packets use `tools/PAN/PUBLISH.PY` for accepted-byte
packaging and the normal `tools/CURRENT` catalog checks. See
[UPAN developer workflow](tools/UPAN/README.MD) and [user controls](docs/PANNING.MD).
The preceding RCPUB producer remains the immutable baseline for older acceptance.

# Building and verifying Windows XT

This is developer guidance. Consumers use [WINXT.ZIP and native DOS Setup](docs/DESKTOP.MD),
or [ordinary Windows Setup with its expanded driver folder](docs/DRIVERS.MD).
The ZIP root is `SETUP.EXE`, `README.TXT` and one `WINXT` folder of real files.
No Python or individual font/grabber/logo gathering is part of installation.
Installed DOS/Windows or original Windows OS media remain required.

## Reproduce the current release

Host packaging uses Python and accepted, already qualified binaries. It does
not launch an emulator or compile native source. Run from this checkout:

```text
python -B tools/PAN/PUBLISH.PY --out NEW-CORE --commit CORE_SOURCE_SHA
python -B tools/PAN/PUBLISH.PY --verify NEW-CORE --commit CORE_SOURCE_SHA
python -B tools/CURRENT/CHECK.PY --core NEW-CORE --sound SOUND-PACKETS --report catalog-check.json
python -B tools/CURRENT/BUNDLE.PY --core NEW-CORE --sound SOUND-PACKETS --commit CATALOG_SOURCE_SHA --out NEW-CATALOG
```

Replace `CORE_SOURCE_SHA` with `core_source_commit` in
`tools/CURRENT/PRODUCTS.JSN`; use the full reviewed checkout commit for
`CATALOG_SOURCE_SHA`. Reproduction must preserve all four published core
identities, including metadata, rather than restamping them with a newer commit.
Use fresh output directories. `--verify` checks the already built directory.

`SOUND-PACKETS` holds the exact ZIPs named by the `sound` entries in
`PRODUCTS.JSN`. Their immutable tracked-source URLs and identities are there;
[current.yml](.github/workflows/current.yml) shows the explicit retrieval and
verification. The curator reads these local files; it does not fetch them.
Original source-build inputs live under `tools/CURRENT/INPUTS` and are emitted
as developer-only `BUILDIN.ZIP`. See [catalog guidance](tools/CURRENT/README.MD).

The core producer emits `WINXT.ZIP`, `WINXTSRC.ZIP`, `WINXT.JSN`, `WINXT.SHA`.
The catalog adds current hardware/app ZIPs and `CURRENT.JSN`/`CURRENT.SHA`.
The CLI in `tools/XR1PACK/PUBLISH.PY` forwards to the core producer; its older
Python helper functions retain historical publisher tests. The standalone
`tools/XRSYNC/PUBLISH.PY` is a retained installation-kit reproducer, not a
second current consumer download.

## Host checks and CI

Choose the checks matching your changes:

| Area | Commands or workflow |
| --- | --- |
| Native core package and preparation boundaries | `python -B tools/DOSINST/TESTPUB.PY`, `python -B tools/XR1PACK/TESTPREP.PY`, `python -B tools/XR1PACK/TESTPUB.PY`; [.github/workflows/xr1pack.yml](.github/workflows/xr1pack.yml) |
| Native CRC implementation | `python -B tools/DOSINST/TESTCRC.PY` compiles a host C check; it uses the mandatory managed GCC launcher on Windows. |
| Tandy grabber installer transaction | `python -B tools/DOSINST/TESTGRAB.PY`; native clipboard and normal-package qualification remain separate. |
| Current HPXY acceptance bindings | `python -B tools/DOSINST/TESTHPXY.PY`; on Windows, `TESTDISP.PY` in the same directory exercises the actual C transaction through the managed GCC launcher. |
| Current catalog and pinned public products | `tools/CURRENT/CHECK.PY` and `BUNDLE.PY` above; [.github/workflows/current.yml](.github/workflows/current.yml) |
| External legacy input adapter | `python -B tools/BUILDDEPS/TESTDEPS.PY` |
| Fixed-profile disk | `python -B tools/FLASHDISK/TESTWAVE.PY`, `TESTFAT.PY`, `TESTPKG.PY`; [.github/workflows/release.yml](.github/workflows/release.yml) |
| PC1512/ColorPlus packets | `python -B tools/DRVSET/VERIFY.PY`; [.github/workflows/driver-packets.yml](.github/workflows/driver-packets.yml) |

For the fixed-disk row, all three scripts are in `tools/FLASHDISK`. Keep
`FAT12_DOSBOX` unset for host-only TESTFAT; enabling its emulator cases requires
the normal coordinated slot. Test success does not imply fresh native execution
or physical-machine acceptance. Preserve the recorded scope of every receipt.

Actions run host checks and assemble pinned artifacts. The historical release
writers in `release.yml`, `winr1.yml` and `softpan.yml` are retired; these workflows
must not be described as creating current GitHub releases automatically.

## Native source builds

The [CGA display source](docs/CGA.MD) adds staging, native builders and
font/control checks under `src/cga/`. With the verified existing display view:

```text
python -B src/cga/TESTCGA.PY --repo DISPLAY-VIEW --out NEW-CGA-HOST
```

For a scheduled native build, create a commit-pinned `--profile cga` source view and follow
[its builder guide](src/cga/README.MD). The CGA access client additionally
requires exact qualified WDESK/WTPLACE source snapshots through BUILDUI.PY
--wdesk/--placement; one WDWIN owner handles root placement and recovery.
The driver build wraps BUILD88 with the shared
watchdog/lease runner. These commands do not qualify a new runtime. The accepted packet, original
reviewed source checkpoint and exact member/evidence pins are in
`tools/CGAPACK/ACCEPT.JSN`; verify them with
`python -B tools/CGAPACK/VERIFY.PY`. Current catalog CI includes that gate.

The PANKEY queue/lifetime API-stub check is `python -B src/cga/TESTKEY.PY --out NEW-KEY-HOST`.
It uses the managed host compiler and makes no native Windows claim.

CGA-specific integration uses `src/cga/INSTALLT.PY` for managed-host C89
transaction checks and `PACKCGA.PY` for the expanded packet. Separate native
`BUILDSET.PY` uses C6 and the existing leased child watchdog, preserving the
published Windows XT SETUP runtime. The [CGA guide](src/cga/README.MD) lists
prepare/build/finalize commands and required native installation/GUI gates.
No consumer Python or support-file gathering is part of that packet.

Main contains no DDK, legacy compiler or emulator. Use the explicit pinned
external inputs and source-view commands in [BUILDDEPS](tools/BUILDDEPS/README.MD).
Only its `fetch` command accesses the network; materialize/verify the locked
bytes, then create a view from a full source commit. No floating DEV/main input.
Use the full checkout for current core/catalog packaging. The adapter's retained
`release` profile is the fixed-profile closure, not the expanded current product;
its historical cleanup/review stages are not new removal instructions.

`src/tandysw/BUILD88.PY` is still a real developer entry point. It builds the
Tandy software-raster driver base (internally called `TR5`), not the complete
current HPXY/desktop product. From the documented
`display` source view, an example is:

```text
python DISPLAY-VIEW/src/tandysw/BUILD88.PY --repo DISPLAY-VIEW --dosbox DOSBOX-X --out NEW-DISPLAY --mode 640x200x4
python -B tools/BUILDDEPS/TESTSRC.PY --view DISPLAY-VIEW
```

Use the actual view/executable paths. The first command runs DOSBox-X and
therefore needs a coordinated lease/owned watchdog; BUILD88 does not acquire
that lease itself. It writes `RESULT.json`, emitted listings and the selected
driver. The second command checks staged source without running a compiler or
emulator. Omitted `--mode` selects 320x200x16; modes and output names are in
`src/tandysw/MODEPROF.PY`. PC1512's `src/pc1512/BUILD15.PY` also uses this
base. Read its explicit `--repo`/`--dosbox`/`--out` interface for that separate build.
A new native build does not replace a qualified runtime or relax package pins.

For the native expanded installer and DOS wrapper, supply external Open Watcom:

```text
python tools/DOSINST/BUILD.PY --watcom C:\WATCOM --target setup --out NEW-SETUP
python tools/DOSINST/BUILD.PY --watcom C:\WATCOM --target wrapper --out NEW-WRAPPER
```

These use 16-bit DOS tools, not host GCC. The Tandy-integrated FIXXT candidate
uses the same Open Watcom builder with `--target finisher`. Its exact source
and binary pins are in `tools/DOSINST/FIXBUILD.JSN`; focused package acceptance
is recorded under `docs/QUAL/TGRAB`. Historical Microsoft C6/LINK4 builds
remain reproducible through:

```text
python tools/SOUNDOWN/FINBUILD.PY --toolchain C6-TOOLCHAIN --dosbox DOSBOX-X --lease SHARED-LEASE --out NEW-FIXXT
```

That command launches a bounded, leased DOSBox-X build. Expanded SETUP pins
are in `SETNAT.JSN`. Earlier `docs/QUAL/DOSINST/EXPAND.JSN` and
`tools/XROEM/NATIVE.JSN` receipts retain their original byte identities.
Preserve guards and qualify changed bytes.

The current HPXY runtime is `tools/DOSINST/BIN/HPXY.DRV`, bound to its
source/build and focused Windows evidence in `tools/DOSINST/HPXY.JSN`.
`docs/QUAL/HPXY/PACKAGE.JSN` qualifies the normal expanded package delta;
older expanded/OEM/panning receipts retain their original byte identities.
The normal producer overlays this qualified HPXY and regenerates native
Setup's file/CRC pins. `FIXXT` also includes `HPXYID.H`, so both full setup
and DISPLAY's optional same-filename refresh use the current driver bytes.
The 127,531-byte HPXY project budget sums NE segment minimum allocations;
its remaining 648 bytes are not free DOS conventional RAM. See the focused
integration report in `experiments/XYSTRIP/INTEGRATION.MD` for actual Windows
heap measurements and the limits of emulator timing.

## Fixed profiles, original fonts and historical sources

```text
python -B tools/FLASHDISK/MAKEIMG.PY --out NEW-FIXED
python -B tools/FLASHDISK/TESTPKG.PY --verify NEW-FIXED
```

This produces the complete `WINXT720.IMG`/`WINXT720.ZIP` data-disk packet,
with the validated grabber, original fonts and startup artwork already included.
See [fixed-profile producer](tools/FLASHDISK/README.MD). Full Windows itself
is not redistributed. The current font generator needs host Python/Pillow,
not vintage Windows font media; [XTFONTS](tools/XTFONTS/README.MD) documents
its `HOST.PY BUILD.PY`/`TEST.PY` commands. Run the host shim on case-sensitive systems.

Historical `oemdisk/MAKEDISK.BAT` and `oemdisk/MAKEDISK.PY` reproduce the old
TANDY88 packet. [oemdisk/HISTORY.MD](oemdisk/HISTORY.MD), older font publishers
and rc.5/rc.6 records retain their original scope; they are not the current
download or support-dependency contract. Never reinstate their external
CGA/EGA font gathering in current installation paths.

The expanded Tandy packet uses `distributions/WINXT/TANDYGR.GR2` and
`TGCLIP.EXE`; older packets retain `CGA.GR2`. Packets include selected
XTC/XTE/XTTSYS fonts, with `XTSTATIC.LGO`/`WXTSPL01.RLE` and other approved
startup assets.
The current [portable OEM descriptor](tools/XROEM/OEMSETUP.INF) selects XTC3;
the full package also supplies the remaining font families. Do not restore
root duplicates, redesign assets or collect stock fonts merely to build a packet.

The single current release is `windows-xt`. Publication is a separate authorized
operation after exact-head CI/review and anonymous asset checks. Preserve core
identities and component notices, update only the qualified affected product,
and retain old tags/assets; superseded release pages are reversible drafts.
