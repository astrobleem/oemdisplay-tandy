# CGA source candidate

This is host-checked development source, not an installable/qualified packet.
See [the coverage audit and native gates](../../docs/CGA.MD). No emulator was
launched for this candidate. No accepted binary, packet or publication pin changes.

## Host work

Use a pinned external display source view for `--repo` (the existing `display`
profile is sufficient for these staging checks). Run the scripts from the
current CGA checkout to test uncommitted work:

```text
python -B src/cga/TESTCGA.PY --repo DISPLAY-VIEW --out NEW-CGA-HOST
python -B src/cga/STAGECGA.PY --repo DISPLAY-VIEW --out NEW-CGA100 --mode 160x100x16
python -B src/cga/CGAFONT.PY --out NEW-CGA-FONTS
```

`TESTCGA` exercises pair colors, clipped writes, capture validation, cursor
edges/buffer bounds, timing constants, independent FNT/NE validation and all
three source stages. Normal modes must match the existing BUILD88 stages
byte for byte. PNGs in the font output are **host specimens**, including a
4:3 display approximation; they are not Windows screenshots or scanout proof.
Generated output uses fresh directories; failed partial stages are not reused.
Developer Python/Pillow never belongs in the consumer installation process.

The four-plane DDK renderer and its source pins are unchanged. STAGECGA uses
the BUILD88 stage order. CGA100.PY adapts only the final 160-wide stage.
The normal profiles use the existing 04h high-intensity palette-1 conversion
and the 06h black/white conversion, including their existing redraw paths.
This does not add palette-0/low-intensity/05h choices or claim IBM acceptance.

## Scheduled native build

First commit the reviewable local source and use `tools/BUILDDEPS/DEPS.PY view`
with that **full commit**, verified locked dependencies and `--profile cga`.
This profile includes the shared native child runner and original font kit.
The builder must run from inside that view:

```text
python CGA-VIEW/src/cga/BUILDCGA.PY --repo CGA-VIEW --out NEW-CGA-BUILD --mode 160x100x16 --hardware ibm-cga --dosbox DOSBOX-X --lease SHARED-LEASE
```

Only run this after an explicit coordinated slot. Repeat separately with
`320x200x4` and `640x200x2`. The existing RUNDOS watchdog acquires the existing
shared lease, refuses conflicting emulators, saves each owned child's receipt
and stops/releases it. The compiler's Tandy DOSBox configuration is a build
environment, not IBM CGA video qualification. BUILD88's instruction, REP-prefix,
link and resource audits still apply. CGABUILD.JSN reports Windows NOT_TESTED.

## Expanded native installer and packet preparation

The host-qualified renderer/font checkpoint remains `32d89b42`. Consumer
integration continues on `work/cga-install`. Published installer runtimes and
normal-mode renderer bytes are unchanged.

`SETUP.C` is the CGA-specific DOS entry for an existing Windows installation.
It finds the expanded `CGA` folder beside its executable, verifies compiled
size/CRC pins and copies only new or byte-identical installed names. The
accepted grabber uses private `CGAGRAB.GR2`, preserving stock `CGA.GR2`.
`CGASET.PY` stages the exact existing T80SET transaction with private CGA
backup/state names. It selects display, System/Fixed/OEM fonts and 286grabber;
160x100 also registers the small Helv/Courier faces and one-pixel borders.
Normal profiles keep XTC fonts and existing font-list entries.

UNDO preserves unrelated later INI edits, changed payloads and files still
referenced by those INIs. Interrupted copies and cleanup are retryable through
this packet's sealed copy record and completed-undo marker. Explicit RESTORE
uses the two safety INIs, losing later INI edits. No legacy migration or
directory-wide cleanup is introduced. Each INI is limited to 20,000 bytes to
leave small-model data/stack headroom; oversized input is refused before copying.

Run the new transaction/packet host checks through the managed GCC launcher:

```text
python -B src/cga/INSTALLT.PY --repo CGA-CHECKOUT --support FULL-SUPPORT-CHECKOUT --out NEW-INSTALL-HOST
```

The explicit support checkout supplies existing pinned fonts, grabber,
startup assets and notices to the developer producer. Consumers receive them
bundled. Synthetic driver fixtures and modern SETUPHOST.EXE are host tests
only; the packet finalizer refuses those fixtures.

After the three scheduled driver builds:

```text
python CGA-VIEW/src/cga/PACKCGA.PY prepare --repo CGA-VIEW --support FULL-SUPPORT-CHECKOUT --build-100 BUILD100 --build-320 BUILD320 --build-640 BUILD640 --source-commit FULL_CGA_SOURCE_COMMIT --out NEW-CGA-PREP
```

Preparation checks all MZ/NE drivers against CGABUILD receipts, generates the
small fonts and includes the pinned XTC fonts, grabber, startup assets and
notices. It emits `packet/README.TXT`, one `packet/CGA` folder, PREPARED.JSN
and private native-src files. Headers and manifests are generated, never
consumer edits. Extra packet/helper-source files are rejected.

In the coordinated native slot:

```text
python CGA-VIEW/src/cga/BUILDSET.PY --prepared NEW-CGA-PREP --repo CGA-VIEW --toolchain C6-TOOLCHAIN --dosbox DOSBOX-X --lease SHARED-LEASE --out NEW-CGA-SETUP
python CGA-VIEW/src/cga/PACKCGA.PY finish --prepared NEW-CGA-PREP --build NEW-CGA-SETUP --out NEW-CGA-PACKET
```

BUILDSET uses C6 `/G0 /AS`, LINK4 and the existing leased watchdog. Its exact
source/binary receipt must match preparation. Finalization rejects host PE
executables and emits CGADEV.ZIP with root SETUP.EXE, README.TXT and CGA/.
It remains a development packet until native install/Windows/GUI gates pass;
no current release or shared installer runtime is replaced.

## Fonts, controls and native acceptance

CGAFONT generates CG1SYS/FIX/OEM and the additional Helv/Courier faces at 4x6,
48x40 logical dpi. The ASCII drawings are original; extended unsupported
characters visibly fall back. OEM box/block primitives reuse XT Pixels.
Retain `tools/XTFONTS/LICENSE` with generated fonts. FNT/FON serialization uses
the existing kit. The adapted driver retains its existing component notices;
the font license is not a license for the DDK, compiler or Windows.

CGAUI reuses COMPACT's BMP writer for six-row caption/system/scroll controls,
checkbox/radio atlas, combo button and menu marks. FONTS.ASM descriptions and
compression metrics are staged with the driver. User/system-control behavior,
OEM atlas interpretation and clickable footprints need native validation.

OEMSETUP.INF is a qualification descriptor for three ordinary Windows Setup
choices. The complete consumer route is the adjacent native SETUP, which also
registers dialog faces. CGA binaries and CGAGRAB/return-from-DOS behavior still
need native qualification. Do not direct users to the descriptor alone, gather
files, edit INIs or run developer font tools. Mode changes occur while Windows
is closed and take effect on the next start.

No panning implementation/branch is changed. Compact metrics alone do not make
every third-party dialog fit 160x100. Program Manager, Notepad Run/Open/Save,
message boxes, File Manager, keyboard traversal and recovery must be shown
reachable before calling this usable. If those fail, the next design decision
is a separately qualified viewport using existing panning work, not a new
general renderer or per-application driver.
