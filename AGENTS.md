# Contributor instructions: Windows XT

## Current product and entry points

Windows XT targets Windows 3.0 real mode on an original Tandy 1000 EX/HX
with normal 640 KB. Other hardware uses its matching packet in
[current downloads](docs/DOWNLOADS.MD). See [BUILDING.MD](BUILDING.MD) for commands.

- **Consumer layout:** current `WINXT.ZIP` contains root `SETUP.EXE`,
  `README.TXT` and one expanded `WINXT` folder. Full installation runs native
  DOS `SETUP UPDATE C:\WINDOWS` or `SETUP FRESH A:\`; later use `C:\STARTXT`.
  Drivers only use ordinary Windows Setup against the same movable folder,
  with its guarded `DISPLAY` and `DISPWIN` entries. See [desktop setup](docs/DESKTOP.MD)
  and [driver setup](docs/DRIVERS.MD). Full preparation needs DOS 3.3+;
  the installed-Windows driver route supports DOS 3.20+.
- **Current core producer:** `tools/DOSINST/RCPUB.PY`; the CLI in
  `tools/XR1PACK/PUBLISH.PY` forwards to it. Current download curation is
  `tools/CURRENT/BUNDLE.PY`, checked by `tools/CURRENT/CHECK.PY` and pinned
  in `tools/CURRENT/PRODUCTS.JSN`.
- **Developer display build:** `src/tandysw/BUILD88.PY` exists and builds
  the five-profile Tandy software-raster driver base (internally called `TR5`)
  from an explicit external DDK/toolchain view.
  It is not a build of the complete current HPXY desktop packet. Supply
  `--repo`, `--dosbox`, a fresh `--out` and the intended `--mode`.
  `src/pc1512/BUILD15.PY` also uses BUILD88 as its base; successful compilation
  does not accept a new driver into any packet.
- **Native helper builds:** `tools/DOSINST/BUILD.PY` uses external Open Watcom
  for expanded SETUP and the DOS wrapper. The accepted current FIXXT build
  uses external Microsoft C6 through `tools/SOUNDOWN/FINBUILD.PY`.
- **Fixed-profile producer:** `tools/FLASHDISK/MAKEIMG.PY` builds the complete
  fixed-profile data disk. `oemdisk/MAKEDISK.BAT` and `oemdisk/MAKEDISK.PY`
  are historical TANDY88 reproduction tools, not current product builders.

Developer Python is allowed. Consumer preparation must never require Python,
a modern-host conversion, manual INI edits or collection of driver support files.
Do not invent automatic hardware detection, installer behavior or qualification.

## Bundled support and preserved identities

- Current packets include their selected original XT Pixels fonts:
  `XTCSYS.FON`, `XTCFIX.FON`, `XTCOEM.FON`; `XTESYS.FON`, `XTEFIX.FON`,
  `XTEOEM.FON`; and `XTTSYS.FON` where required. The HPXY OEM descriptor
  `tools/XROEM/OEMSETUP.INF` selects the three XTC fonts with `200,96,48`.
  Stock `CGASYS.FON`, `CGAFIX.FON` and `CGAOEM.FON` are not consumer inputs.
- The authoritative expanded grabber is `distributions/WINXT/CGA.GR2`.
  Do not restore a loose root duplicate or ask consumers to find one.
  Current driver sources also bundle their selected `XTSTATIC.LGO` and
  `WXTSPL01.RLE`; the full/fixed packets carry their additional startup assets.
  Keep the approved artwork selection and each packet's closed support inventory.
- Installed DOS/Windows and normal OS installation media remain prerequisites.
  The full installer gathers OS files from that media; fonts, grabber and logos
  supplied by our driver packets are a separate set. Historical media-gathering
  contracts in [oemdisk](oemdisk/HISTORY.MD), [MODES](docs/MODES.MD) and
  [OEMDISK](docs/OEMDISK.MD) must not be reapplied to current packets.
- Preserve accepted runtime binaries, source/evidence pins, component notices
  and original test records. Never relax pins or replace accepted bytes merely
  because a developer rebuild or oracle passes. Runtime changes need separate
  qualification and complete affected manifest/recipe updates.
  This also preserves `src/tandysw/bin/` and the older OEM pins; BUILD88
  development outputs must not overwrite those frozen accepted binaries.
- Source rebuilds use explicit commit-pinned external views from
  [BUILDDEPS](tools/BUILDDEPS/README.MD). Main does not bundle the DDK/compiler
  or emulator. Keep OS media, installed/prepared guest trees and unrelated
  toolchains out of public artifacts. Preserve each component's actual notices;
  do not apply a blanket project license to adapted components.

## File handling and native code

- Preserve CRLF. DOS payload names must fit 8.3; uppercase is preferred.
  Existing host-only names such as `REPCOPY88.PY` are not DOS payloads.
- Target 8086/8088 instructions. MASM source uses MASM 5.1 syntax, Pascal
  calling convention (`?PLM=1`), uppercase exports and `cmacros.inc` segment
  macros. Native C code uses the target toolchain's C89-compatible conventions.
- Preserve NEAR/FAR linkage. For L2022/L2023 or fixup overflows, inspect the
  emitted listings, DEF/export aliases and existing `externNP`/`externFP`
  contracts rather than changing the calling convention globally.
- Windows host GCC/G++ and their compiler children must use the managed
  `%USERPROFILE%\Documents\Codex\toolchains\gcc-ucrt64.py` launcher.
  This is separate from the native Open Watcom and DOS MSC6 routes. Do not
  change global PATH or substitute raw host GCC for a 16-bit DOS compiler.

## Hardware and fixed-profile contracts

- Preserve normal 640 KB and real-mode operation; no 386, expanded-memory,
  EMS/XMS or UMB workaround. Never bypass a failed reservation/ownership guard.
- The fixed profiles are 320x200x16, 640x200x4 black/red/green/white,
  160x200x16, 320x200x4 black/cyan/magenta/white and 640x200x2 black/white.
  `src/tandysw/MODEPROF.PY` maps these source-build outputs to
  `TANDY88.DRV`, `TNDY6404.DRV`, `TNDY160.DRV`, `TNDY3204.DRV`, `TNDY6402.DRV`.
- BIOS 0Ah is four colors on original EX/HX, never 640x200x16. Keep four
  logical DDB planes and report the actual palette through NUMCOLORS.
  Fixed-profile shadow sizes are 16,000/32,000/64,000 bytes by width;
  video buffers are 16,384 bytes except modes 09h/0Ah at 32,768 bytes.
- Fixed 320x200x16 uses XTE font metrics `133,96,72`; the other graphics
  profiles use XTC metrics `200,96,48`. Preserve font resource metrics and
  Setup selection, not historical stock-font filenames as external dependencies.
- The shared RESERVE helper protects video overlap before Setup/startup.
  Lower-color modes do not authorize bypassing the launcher. Fixed-profile
  tests can start from stock CGA and select 640x200x4 for a wider Setup;
  low-resolution dialogs can clip.
- Keep historical cyan/magenta `docs/modes/6404` evidence distinct from
  current red/green `docs/modes/6404rg`. Mathematical/oracle checks do not
  establish full Windows or physical-hardware coverage. NULL-buffer
  GetDIBits remains unsupported; use each packet's recorded native scope.

## Tests, emulator use and publication

Run the checks for the changed producer; [BUILDING.MD](BUILDING.MD) maps them
to current workflows. Actions package pinned bytes and run host checks;
they do not assemble/link new DOS driver binaries. Use the current lowercase
TSHELL idle/Hold suite; do not recreate its historical case collision.

An emulator requires an explicit coordinated slot, the shared lease, private
image/config, owned-process watchdog and verified stop/release. Older build
scripts' timeouts do not acquire the shared lease. Never launch concurrently,
stop an unknown process, use CF hardware or turn a harness timeout into PASS.
Use headless controls; retain failed receipts and distinguish software checks
from physical scanout. Choose a bound that accommodates measured preparation.

The current release is `windows-xt`. Current workflows verify and upload
Actions artifacts; retired milestone release writers must stay retired.
Follow the current publication authorization, exact-head review and CI gates.
Preserve the four pinned core assets when curating other products, retain
source/build-input access, and never move/delete old tags or release assets.
Superseded release visibility is managed reversibly, not by deleting history.
