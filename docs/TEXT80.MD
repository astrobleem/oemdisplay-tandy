# TEXT80: Windows 3.0 in 80-column text mode (experimental)

Branch `ai/text80` (TXT40 + XTPAN merged in), draft PR. Nothing here
changes a released driver, an installer default, a package, a pin or a
release hash. A rebuild is not runtime acceptance: everything below was
run in emulators, none of it on real hardware yet.

@@VERDICT@@

## 1. Profiles

| Profile | Driver | Text on screen | Glyph cell | Windows sees | Pixel aspect GDI is told | Adapters | Minimum hardware |
|---|---|---|---|---|---|---|---|
| TXT40 (existing, fixed here) | `TXT40.DRV` | 40x25 | 8x8 | 320x200 | as TR5 320x200 | CGA-compatible colour | 8088, CGA, 640 KB |
| **TEXT80 25** | `TEXT80.DRV` | 80x25 | 8x8 (BIOS font of the card: 8x8 CGA, 8x9 Tandy, 8x14 EGA, 8x16 VGA) | 640x200 | 96x48 (the CGA resolution resources) | CGA, Tandy 1000/PCjr-class, EGA, VGA in their colour 80x25 mode | 8088, any of those, 640 KB |
| **TEXT80 PAN** | `T80PAN.DRV` + `XTPAN.EXE` | 80x25 window over 80x50 logical rows | as above | 640x400 | 96x48 | as above | 8088, 640 KB (130 KB more Windows memory than 25) |
| **TEXT80 VGA** | `T80VGA.DRV` | 80x50 | 8x8 (INT 10h AX=1112h ROM font, 400 scan lines) | 640x400 | 96x48 | VGA only (checked) | 8088 with an 8-bit VGA card, 640 KB |

Physical text cells versus logical pixels: Windows always draws 8x8
logical pixels per text cell. How tall a cell looks is the adapter's
business (8x9 on a Tandy 1000 HX in 80 columns, 8x16 on VGA 80x25). The
logical pixel aspect told to GDI is the CGA resolution set's 96x48, so the
system font and the added 8x8 faces are chosen; circles drawn by programs
are taller than wide on every profile.

Capability checks in Enable (no assumptions):
- 25 and PAN: BIOS mode 03h; CGA-compatible mode register 3D8h = 09h
  (blink off) and BIOS 40:65h; on EGA/VGA (INT 10h AH=12h BL=10h answers)
  blink off with INT 10h AX=1003h. The Tandy 1000 EX/HX and PCjr-class
  video run 80x25 colour through the BIOS like a CGA. Real IBM CGA shows
  snow in 80 columns when video memory is written during the display (the
  presenter writes only the cells that change; it does not wait for
  retrace).
- VGA: INT 10h AX=1A00h must return AL=1Ah and display combination 7 or 8
  (VGA mono/colour), checked before the mode is touched; then mode 03h,
  INT 10h AX=1112h (8x8 font), and the BIOS must report 50 rows (40:84h =
  49), else mode 03h is restored, the shadow freed and Enable returns 0.
  UEFI machines without a legacy video BIOS cannot run real-mode Windows
  3.0 anyway; VGA text through a CSM is the same INT 10h path and has not
  been tried.

## 2. Where Notepad's 3-second keystroke went (TXT40), and the fixes

@@PROFILE@@

## 3. Memory

@@MEMORY@@

## 4. Panning (PAN profile)

@@PAN@@

## 5. VGA 80x50

@@VGA@@

## 6. Tests and evidence

@@TESTS@@

## 7. Installing and removing (DOS)

From the folder holding the TEXT80 files, at the DOS prompt (never inside
Windows):

    T80ON [windows folder] [25 | PAN | VGA]      (defaults C:\WINDOWS and 25)
    T80OFF [windows folder]

`T80ON` copies the driver and the 8x8 fonts into the Windows SYSTEM
folder (and, for PAN, `XTPAN.EXE` into the Windows folder), then
`T80SET ON` saves `SYSTEM.INI` and `WIN.INI` byte for byte as
`SYSTEM.T80` and `WIN.T80` and edits the live files:
- `SYSTEM.INI [boot]`: `display.drv=` the chosen driver;
  `fonts.fon=XTTSYS.FON`, `fixedfon.fon=XTCFIX.FON`,
  `oemfonts.fon=XTCOEM.FON` (the first-party 8x8 fonts);
- `WIN.INI [windows] load=`: for PAN, `XTPAN.EXE` is appended; every
  existing entry stays (checked in 86Box with `T80SNAP.EXE` and, on the
  Tandy HX disk, `XTPAN.EXE` already on the line);
- `WIN.INI [fonts]`: two lines are **added**, none removed or commented
  out: `Helv 8x8 (TEXT80)=T80HELV.FON` and
  `Courier 8x8 (TEXT80)=T80COUR.FON`.

`T80ON` refuses if `SYSTEM.T80` already exists. `T80OFF` copies both
backups back over the live files and deletes them, so Windows starts
exactly as before (checked in every 86Box session, including after the
forced allocation failure). The copied driver and fonts stay in SYSTEM,
unused. Everything works from the DOS prompt, so a display driver that
cannot start Windows cannot lock you out.

Why the two added faces: Windows 3.0 dialogs ask for bold "Helv 8"; the
installed `HELVB.FON` strikes are 10 pixels tall and proportional, which
cannot be shown as text cells. `T80HELV.FON` is the 8x8 system-font strike
renamed "Helv", offered as **bold** and **variable pitch** (all glyphs 8
pixels wide): with a normal-weight face GDI simulated bold by drawing each
label twice one pixel apart, and a fixed-pitch face lost to `HELVB.FON`
on the pitch penalty (both seen in 86Box with the ExtTextOut trace before
they were fixed). TXT40's earlier test disks commented out the whole
`[fonts]` list instead; TEXT80 never does.

Application limits: text shows as text only in 8-pixel-high faces (the
system, OEM and fixed fonts and the two added faces). A program that asks
for a bigger face (Write, Paintbrush text, Help titles, Tms Rmn, Helv 10
and up) gets an EGA-resolution strike that is drawn into the shadow
correctly but shown as block and shade approximations. Graphics
(Paintbrush, icons, wallpaper) are always approximations. Help, Write and
Cardfile were not tried.

## 8. Building

@@BUILD@@

## 9. Limits and open questions

@@LIMITS@@

## 10. What to test on real hardware

@@HARDWARE@@
