TANDY WINDOWS 3.0 REAL 80x25 TEXT-MODE PROOF

STATUS: isolated feasibility experiment. It is not a finished replacement
for the accepted Tandy graphics driver. Keep it out of your normal Windows
installation and OEM/Setup disk. It is not yet suitable for everyday use.

What is proved
- Actual BIOS mode 03h, 80 columns, 25 rows, 2000 B800 character/attribute cells.
- Unchanged Windows 3.0 Program Manager and Notepad run in real mode.
- Notepad title, menus and both demonstration lines are readable hardware text.
- Full repaint retains those lines. Logical GDI pixels, XOR and screen copy
  tests pass, including pixel correctness after a saved bitmap is restored.
- The assembler listing audit checked 13,650 emitted instruction rows, with
  no unsupported 8086/8088 instructions. Physical hardware remains untested.

Important failures and limits
- Bitmap-only restore loses semantic characters: final native test measured
  60 changed hardware bytes despite zero sampled GDI pixel mismatches.
- Moving a window, sub-cell clipping and caret/inversion can damage text.
- Program Manager's title and menus are readable, but small icon labels and
  arbitrary graphics are approximate. This is not broad app compatibility.
- The mode has 640x200 logical pixels over an 80x25 hardware grid. It is a
  pixel-preserving shadow plus a lossy character presenter, not a DOS clone
  of Notepad or a screenshot displayed inside a text-mode shell.

Contents
TXTMODE.DRV: experimental driver, 72,960 bytes.
SOURCE: build/port sources; requires the original project's DDK, tools and
support inputs. No Microsoft compiler, SDK/DDK binaries or Windows media.
PROBE: automated native probe and its first-party executable/source.
FIXFONT.PY: constructs the private fixed-cell system font from your own
CGASYS.FON and CGAFIX.FON. It refuses unknown input hashes. No fonts included.
EVIDENCE: actual B800 snapshots, decoded images/text, native logs, build and
status JSON. Images use the BIOS font dump solely for local decoding; ROM
and Windows font bytes are not distributed. No generated/mockup UI is used.

Lab reproduction, not normal installation
1. Work only in a disposable COPY of your owned Windows 3.0 installation.
2. Build using SOURCE/BUILD88.PY and the original project layout, with
   --mode 640x200x2, --dosbox <DOSBox-X> and a new --out directory.
   Keep SOURCE under src/tandysw in an isolated project copy; provide its
   existing BIN, LIB and DDK directories. Do not replace accepted graphics
   binaries or change the normal project launcher.
3. The lab uses display.drv=TXTMODE.DRV, fonts.fon=CGASYS.FON,
   fixedfon.fon=CGAFIX.FON, oemfonts.fon=CGAOEM.FON in the COPY only.
   Run FIXFONT.PY <original CGASYS> <owned CGAFIX> <private CGASYS copy>.
   Keep original module identity: directly using CGAFIX as both system and
   fixed font was not a working configuration in this test.
4. Use machine=tandy, normal core, cputype=8086_prefetch, 640KB base memory,
   XMS/EMS/UMB disabled, FPU disabled and WIN /R. The evidence used accelerated
   fixed 200000 emulator cycles; this is not 4.77MHz performance validation.
5. The automated probe was loaded via the COPY's WIN.INI load= entry. It
   starts untouched Notepad, sets sample edit text, tests repaint/movement
   and bitmap restoration, logs, then closes its test window and Notepad.
   This does not stand in for manual keyboard/mouse or physical Tandy tests.

Next required work
Semantic text must follow clipped regions and DDB/bitmap transfers, rather
than living only at the most recently drawn screen cell. An all-fixed-cell
font/layout contract and more complete repaint/restore invalidation are
needed before this can become a practical driver.
