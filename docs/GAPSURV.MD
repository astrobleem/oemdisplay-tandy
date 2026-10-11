# Survey: XT-class display hardware that Windows under-used

The Tandy story in one line: the hardware could show 16 colors, but stock
Windows 3.0 treated it as CGA and showed 2. This survey looks for the same
pattern elsewhere: real-mode-capable (8086/8088) machines or cards whose
display hardware went well beyond what any Windows driver used. It ranks
them by how much of this repository's existing work carries over.

Sourced facts are linked at the end. "Not found" means this survey found no
driver, not that one never existed; corrections are welcome.

## Summary

| Rank | Hardware | Hardware can do | Windows used | Fit with this codebase |
| --- | --- | --- | --- | --- |
| 1 | IBM PCjr | 320x200x16, 640x200x4 | CGA-class | Very high: same modes and banks; see [PCJR.MD](PCJR.MD) |
| 2 | Plantronics ColorPlus family (ATI Graphics Solution/"Small Wonder", Paradise EGA 480 in CGA mode as in the Amstrad PC1640, some Tandy cards) | 320x200x16, 640x200x4 | CGA. A community Windows 3.0/3.1 driver for 640x200x4, [WINPCP](https://github.com/cluehawk/WINPCP), is in early development; GEM had 640x200x4 | High: same color depths as TR5 profiles; only the flush layout (two 16KB planes at B800h/BC00h via port 3DDh) changes, and video RAM is on the card, so no shared-RAM reservation |
| 3 | Tandy 1000 SL/TL/RL Video II | 640x200x16 | EX/HX-class modes at best | Medium: new 64KB linear target; see [TGA2.MD](TGA2.MD) |
| 4 | Amstrad PC1512 | 640x200x16 (four color planes on a CGA base) | Windows up to 3.0 runs; no dedicated driver found. GEM supported the mode | Medium: the four-plane DDK shadow already matches its plane model; 640-wide shadow is 64,000 bytes |
| 5 | Olivetti M24 / AT&T 6300 with the graphics memory expansion | 640x400 with up to 16 colors | 640x400 treated as monochrome | Low-medium: a 640x400 four-plane shadow (128,000 bytes) does not fit one real-mode segment; needs direct rendering |
| 6 | IBM PS/2 Model 25/30 (8086) MCGA | 320x200x256 | Windows 3.0 drove MCGA as "VGA mono" 640x480x2 | Low: needs a packed 8-bit driver family, not the four-plane one |
| 7 | 8088 machines with an SVGA chip (including PicoGraph's CL5429 module) | 800x600x16 and beyond | Windows 3.0 real mode: standard VGA 640x480x16 | Medium-high for 800x600x16: see below |
| - | Hercules InColor | 720x350x16 (64-color palette) | Hercules shipped a Windows driver; version coverage unclear | Low priority: vendor support existed |
| - | CGA composite artifact color | ~16 artifact colors | CGA mono | Curiosity only; depends on monitor |

## Notes per entry

**PCjr.** The cleanest win. Started in [PCJR.MD](PCJR.MD) with emulator
evidence and a three-edit staged source.

**Plantronics ColorPlus family.** The most interesting surprise: it offers the
same two color upgrades as the Tandy (320x200 at 16 colors, 640x200 at 4),
on ordinary CGA-class cards. The 32KB of video RAM lives on the card at
B8000h as two planes (second plane normally at BC000h); you set a normal CGA
graphics mode, then turn on the extended mode with bits 4-6 of port 3DDh.
Because the TR5 driver already keeps a private shadow and converts on flush,
a Plantronics profile is mostly a new flush/cursor layout plus detection.
Software support was thin (CompuShow, GEM drivers for 640x200x4). WINPCP
(MIT, last commit 2026-02-07) targets 640x200x4 only; at that commit it has
stubs and text-expansion code but no Enable, BitBlt or cursor yet, and it
assembles as .186 (V20), so it is not 8088-safe as written. Its notes record
the hardware facts this survey needs: 320x200x16 is BIOS mode 5 plus 3DDh =
10h, with red/green bits at B800:0000 and blue/intensity bits at B800:4000,
2 bits per pixel each, CGA even/odd interleave. A 320x200x16 Plantronics
profile here would not overlap WINPCP's 640x200x4 goal.

**Amstrad PC1512.** An 8MHz 8086 with a CGA-compatible chip extended to
640x200 in 16 colors using four color planes. GEM, bundled with the machine,
supported its custom graphics. Windows up to 3.0 ran on it; no 16-color
Windows driver was found.

**Olivetti M24 / AT&T 6300.** The built-in 640x400 modes are monochrome
(one foreground color). An add-on graphics memory board (32-96KB) gives
most modes 16 colors, including the 640-pixel modes. Software used 640x400
monochrome moderately (Lotus 1-2-3, Symphony); color use was rare.

**MCGA.** Windows 3.0's own DDK lists MCGA under the one-plane drivers as
"VGAmono", i.e. 640x480 in two colors, while the hardware's signature mode is
320x200 in 256 colors. A 320x200x256 real-mode driver would be a novelty
with a tiny desktop, comparable to the 160x200 Tandy profile.

**Hercules InColor.** Included for completeness. Hercules bundled drivers
for Lotus, AutoCAD, WordPerfect and Windows, so the gap is smaller.

## PicoGraph: new hardware for old machines

[PicoGraph](https://github.com/ianhan/picograph) is firmware for FreddyV's
PicoMEM 8-bit ISA board (a Pico 2 on PicoMEM v1, or PicoMEM2 as-is). It
emulates a display adapter on the ISA bus with PCem-derived code and sends the
picture to a USB DisplayLink adapter. One module is built into each firmware
image (`PICOGRAPH_MODULE`). Modules at commit `1de901d` (2026-09-10):
CL5429 (Cirrus CL-GD5429, PCem-based), VGA, EGA, Hercules, MDA, a Sony
DTL-H201A PlayStation development board, a passive VGA/MCGA register viewer,
and a sample module.

What it means for this project:

1. **Stock drivers first.** With the EGA or VGA module, an XT should already
   run Windows 3.0 real mode with Microsoft's own EGA/VGA drivers. That is
   the baseline to measure (DisplayLink scan-out latency and dirty tracking
   under GDI workloads) before writing anything.
2. **The real gap: SVGA on an 8088.** The CL5429 module emulates up to
   1024-pixel-wide displays, planar 4bpp, packed 8bpp and 15/16/24-bit
   modes, with bank registers. Windows 3.1 requires a 286, so an 8088 owner
   is limited to Windows 3.0 real mode, whose stock choice is 640x480x16 VGA.
   **800x600x16 needs no banking** (60,000 bytes per plane fits the 64KB
   A0000h window), so a real-mode 800x600x16 driver could start from the
   DDK's four-plane VGA driver with a wider stride and a Cirrus mode set.
   That is the PicoGraph equivalent of the Tandy 4-to-16 color fix, and it
   would also help 8088 owners with real Cirrus/Tseng-class cards.
3. **A Tandy/PCjr/Plantronics module for PicoGraph.** PicoGraph has no CGA
   family module yet. A module implementing Tandy video (ports 3D0h-3DFh,
   the video array, 32KB at B8000h) or the simpler Plantronics extension
   would give any XT the TR5 driver's color modes, with video RAM on the card
   and therefore no shared-memory reservation. That would turn "Windows XT
   for Tandy owners" into "Windows XT for every XT with a PicoMEM".
4. **Inside a Tandy.** EX/HX have only Tandy PLUS slots; SX/TX/SL/TL have
   8-bit ISA slots. EGA/VGA color modes decode the same 3D4h/3DAh ports as
   the Tandy's built-in video, so the built-in video must be disabled or the
   module kept in a monochrome/3B4h configuration. Needs a hardware check per
   model before any claim.

Proposed order: (1) measure stock Windows 3.0 EGA/VGA on PicoGraph,
(2) real-mode 800x600x16 driver for CL5429, (3) propose a Tandy-video module
upstream to PicoGraph.

## Sources

- [Tandy Graphics Adapter (Wikipedia)](https://en.wikipedia.org/wiki/Tandy_Graphics_Adapter)
- [Plantronics ColorPlus notes (seasip.info): modes, port 3DDh, compatible cards, software](https://www.seasip.info/VintagePC/plantronics.html)
- [Amstrad PC1512 (Wikipedia)](https://en.wikipedia.org/wiki/Amstrad_PC1512)
- [Amstrad PC1512 graphics programming (retroisle)](https://retroisle.com/amstrad/pcs/Technical/Hardware/PC1512_Video.php)
- [Olivetti M24 (Wikipedia)](https://en.wikipedia.org/wiki/Olivetti_M24)
- [Windows 3.0 DDK installation and update guide (PCjs): display driver families incl. "MCGA (VGAmono)"](https://www.pcjs.org/documents/books/mspl13/win/w3ddkins/)
- [Hercules InColor Card (Wikipedia)](https://en.wikipedia.org/wiki/Hercules_InColor_Card)
- [PicoGraph repository and module sources](https://github.com/ianhan/picograph)
- [PicoMEM hardware](https://github.com/FreddyVRetro/ISA-PicoMEM)
