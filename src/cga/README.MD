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

## Fonts, controls and installation work still gated

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

OEMSETUP.INF is a portable **source candidate** for three ordinary Windows
Setup choices. It is not a complete consumer packet: CGA driver binaries do
not exist yet, the additional dialog faces still need native DOS installation
integration, and CGA.GR2/return-from-DOS behavior needs qualification. Do not
tell consumers to gather these files, edit INI files or run font tools. The
eventual packet must bundle every selected font, grabber and existing startup
asset and perform font registration/recovery natively. Mode changes go through
Setup while Windows is closed and take effect on the next Windows start.

No panning implementation/branch is changed. Compact metrics alone do not make
every third-party dialog fit 160x100. Program Manager, Notepad Run/Open/Save,
message boxes, File Manager, keyboard traversal and recovery must be shown
reachable before calling this usable. If those fail, the next design decision
is a separately qualified viewport using existing panning work, not a new
general renderer or per-application driver.
