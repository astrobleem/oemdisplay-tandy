# XT Pixels original bitmap font kit

Original MIT-licensed bitmap replacements for the six English Windows 3.0
font dependencies, plus the independently generated fixed TXTSYS strike.
R10 passed host format/reproduction/GDI checks, all-byte native graphics
checks, five graphics modes, and both default and explicit /VERIFY native
preparation/Setup/cold-start/exact-rollback transactions on 2026-10-09.
This is the rc.5 prerelease font candidate. Release QUALIFY.JSON binds the
qualification to exact disk, helper, installer, source and font hashes.
BUILD.JSON and REBUILD.JSON are preserved pre-native build snapshots; their
false native qualification flags are superseded only by that final record.

## Build on a modern host

Python 3.8+ and Pillow are used on the host; Pillow produces PNG specimens.
FNT/FON serialization uses Python's standard library and the checked-in
numeric CONTRACT.JSON. No Windows font media, installed font rasterization,
compiler or emulator is required to generate the original fonts.

```
python tools/XTFONTS/HOST.PY BUILD.PY --out NEW-FONTS
python tools/XTFONTS/HOST.PY TEST.PY --out NEW-FONTS
python tools/XTFONTS/HOST.PY HOSTGDI.PY --out NEW-FONTS
```

Use a fresh output directory. HOST.PY supports uppercase source imports
on case-sensitive hosts while preserving the original generator files.
HOSTGDI requires modern Windows. Change the
hand-authored grids/rules in GLYPHS.PY and BUILD.PY to edit glyphs. No Python,
Pillow or font generation is needed on the vintage computer. Packaged names
use XTC*/XTE*/XTTSYS to prevent Windows Setup retaining installed same-name
Microsoft fonts. These are byte-identical aliases, not changed resources:

| Inspected dependency | Packaged original | NE module | FONT ID | Charset | Cell | Ascent | Int/ext leading |
| --- | --- | --- | ---: | ---: | --- | ---: | --- |
| CGASYS.FON | XTCSYS.FON | FONTS | 27 | ANSI 0 | proportional x8 | 7 | 1/0 |
| CGAFIX.FON | XTCFIX.FON | FIXFONTS | 27 | ANSI 0 | 8x8 | 7 | 0/1 |
| CGAOEM.FON | XTCOEM.FON | OEMFONTS | 29 | OEM 255 | 8x8 | 7 | 0/0 |
| EGASYS.FON | XTESYS.FON | FONTS | 28 | ANSI 0 | proportional x12 | 10 | 2/0 |
| EGAFIX.FON | XTEFIX.FON | FIXFONTS | 28 | ANSI 0 | 8x10 | 9 | 2/0 |
| EGAOEM.FON | XTEOEM.FON | OEMFONTS | 29 | OEM 255 | 8x8 | 7 | 0/0 |
| TXTSYS.FON (generated) | XTTSYS.FON | FONTS | 27 | ANSI 0 | 8x8 | 7 | 0/1 |

CONTRACT.JSON contains inspected numeric metrics/advances and resource
identities, never original glyph bitmap data. INSPECT.PY optionally repeats
the read-only contract inspection against explicitly supplied owned files.
The generator does not run INSPECT or read those files.

System retains average width 7, maximum width 14, weight 700, every advance,
baseline and leading. Fixed/OEM metrics are retained too. EGA OEM really has
the same 8x8 FNT as CGA OEM, and the new OEM FON files are byte-identical.
Every FON contains FONTDIR 1, its FONT resource and a FONTDIR NAMETABLE alias.
Resource-only NE headers, correct empty module/import tables, DOS stub,
directories and glyph payloads are generated anew. FNT 0200h uses 16-bit
offsets. Even dfWidthBytes storage strides differ from the original odd
strides; dialog metrics and character advances do not change.

## Encoding and missing characters

ASCII and Latin-1 printable characters are drawn, with early Windows ANSI
smart quotes, ligatures, S-caron and Y-diaeresis. Reserved ANSI bytes
7F,80,81,8D,8E,8F,90,9D,9E contain visible fallback boxes. No Euro, later ANSI
additions, Unicode emoji or supplementary characters are claimed. Exact
coverage and missing-byte records are in BUILD.JSON and MISSING.JSON.

OEM has original CP437 drawings in the advertised 01..FE range: control
pictures, Latin, Greek/math, box tracks, shades and blocks. ANSI's default is
80; outside-range input maps there. OEM's default/break is 20 (space), so
00/FF render blank for compatibility. Native direct-byte tests verified all
256 bytes for each stock font, including reserved and out-of-range behavior.
Modern host GDI maps five reserved ANSI bytes differently during Unicode
translation; HOSTGDI.JSON records this separately from native Win16 results.

## Validation and previews

TEST.PY passed 1404 glyph boundary checks, 72 corruption refusals and 28
byte-identical rebuilt outputs. HOSTGDI loaded temporary unique aliases,
checked all six strikes' metrics and normal ANSI/all OEM glyph pixels, and
removed every temporary font in finally cleanup. Existing host System was
never replaced. Native complete-byte tests covered all six original strikes
plus TXTSYS in graphics, including all advances and default substitution.

Native System/Fixed/OEM loading, metrics and tested pixels passed in 160x200,
320x200 and both existing 640x200 graphics modes. Default and /VERIFY native
transactions used a preparation fixture containing no Windows font sources;
seven staged own fonts and the three installed selections matched exactly.
Cold Win3 GDI rendered our System, Fixed and OEM pixels. Both transactions
restored 113 original Windows files, both boot files and deliberate INI edits.
Default SHA/readback/comparison counters were zero. Explicit /VERIFY had
positive SHA, output-readback and comparison counters. The exact final 720K
FAT12 image and ZIPs passed package allowlist, pins, checksums and reproduction
tests. See final EVIDENCE and QUALIFY.JSON for records and recovered attempts.

SPECIMENS contains native-size host FNT decodes, glyph atlases and modern
Windows GDI renders. PREVIEWS contains genuine Windows 3.0 emulator captures,
with captions identifying the run and resolution. These categories must not
be confused. The representative 640 capture predates filename aliases but
uses identical R10 font bytes; the final alias transaction capture is 320.

At 160 pixels menus wrap and the 218-pixel probe dialog clips. A private
original-font control reproduced identical geometry and clipping. At 320/640
that probe fits and button labels fit. This does not qualify every Windows
dialog or physical 8088 timing. Tests used Tandy 640KB/8086 real-mode emulation,
no XMS/EMS/UMB. Experimental TXTMODE retains known extended-character and
adjacent-cell corruption; loading/advances and ASCII primary cells passed,
but its display is not visually qualified. No ROM bitmap atlas was extracted.

## Provenance and scope

Glyphs were authored on 2026-10-09 without viewing, extracting, tracing or
rasterizing Microsoft, ROM or installed font bitmaps. Generic Latin forms
and algorithmic box/block shapes are original grid drawings. Numeric metrics
are compatibility facts. No third-party glyph source is incorporated.
GLYPHS.PY, the font tools and generated XT Pixels FNT/FONs are MIT licensed;
include LICENSE when redistributing. Other suite components retain their
existing licenses. No Windows or compiler binaries are in the source kit.

Font-format references: Microsoft's archived SDK article Q65123 (FNT 2.x)
and https://learn.microsoft.com/en-us/windows/win32/menurc/fontdirentry.
Local contract inspection verifies actual file identities and metrics.

INTEG.PY prepares a source overlay from an explicitly supplied qualified
baseline, ALIAS.PY assigns the separate 8.3 names, and PINBUILD.PY couples
recompiled PREPXT/TINST binaries to their source/pins. NEXT.PY/ROUND.PY are
private-fixture native harnesses; launching an emulator still requires an
explicit bounded exclusive slot. Saved native framebuffer validation with
NATIVEQA.PY and ENCQA.PY launches no emulator.

Font replacement removes Windows font-source and vintage-Python dependence.
Windows itself, CGA.GR2, CGALOGO.LGO and other non-font dependencies remain.
These are neither included nor made redistributable by the font license.
The explicit publication instruction authorizes rc.5. Existing Windows,
CF, accepted candidates, older release assets and tags remain unchanged.
See ../../docs/FONTS/README.MD for current qualification and download links.
