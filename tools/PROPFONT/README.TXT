WINDOWS XT PROPORTIONAL FONTS

Three extra application typefaces, each at 8 and 12 pixels:
  T1P8 / T1P12   XT Tandy I   - classic Tandy 1000 Video I
  T2P8 / T2P12   XT Tandy II  - classic Tandy 1000 Video II
  TKP8 / TKP12   XT Tandy 2K  - lighter Tandy 2000 graphics

These have real variable character advances. They do not replace System,
Fixed or Terminal, or change any display/installer defaults. The existing
CG1HELV (5 rows), CG2HELV (6 rows) and CG6HELV (8 rows) Helv fonts are also
included under their original names, with unchanged glyph and metric
resources. All nine files have Windows 3.0 Control Panel installation labels.

INSTALL: Extract into a DOS-accessible folder. In Windows 3.0, open Control
Panel, Fonts, Add. Select that folder, select the fonts, and add them.
Use an application's font selection to choose XT Tandy I, XT Tandy II,
XT Tandy 2K or Helv. Applications which only use System will not change.
Close/reopen an application if its font list has not refreshed.

The three CG* files share the existing Helv family. Add them only if you
want their compact Helv choices, which can affect existing applications
and dialogs. Select only T*.FON to add the six Tandy files without Helv.

CHOOSING A SIZE
  160x100 fixed or viewport: compact Helv 5; 6 if extra height is useful.
  160x200: compact Helv 5/6 for more text; Tandy 8 for larger text.
  320x200: compact 6 or Tandy 8; Tandy 12 for the taller sixteen-color UI.
  640x200: Tandy 8. The same applies to HPXY's 640x256 desktop.
  640x400 PCjr/ColorPlus panning: Tandy 12 or 8 for denser text.
Panning dimensions describe the desktop, not additional physical pixels.
Windows point sizes depend on the selected display's DPI. Applications
which request a specific bitmap pixel height can select 5, 6, 8 or 12.
For exact pixels across different display DPIs, programs must also request
the font average width. With width zero, Windows can adjust the aspect ratio.

TEXT80 and TXT40 remain fixed-cell displays. These optional proportional
fonts are intended for graphics drivers, not a text-mode driver upgrade.
Small screens can still clip application dialogs; no font can guarantee
that every program fits. No display driver or system font is replaced.

The Tandy artwork comes from VileR's Oldschool PC Font Pack v2.2. The new
fonts remove blank side bearings, add one pixel of character spacing,
map CP437 artwork to Windows ANSI, and use original XT Pixels artwork for
ANSI characters not present in CP437. The 12-row versions use a deliberate
vertical row map. Reserved Windows 3.0 ANSI bytes show a fallback box.
The compact 5/6-row fonts retain their ASCII-only artwork and extended
placeholders. CG6HELV retains the full XT Pixels 8-row artwork.
Keep LICENSE.TXT and FONTLIC.TXT with these fonts.

Windows 3.0 real-mode emulator checks passed for all five Tandy graphics
modes and CGA 160x100: font loading, all-byte pixels, widths, text extents
and unchanged stock fonts. Physical hardware is not qualified by these tests.

Source and builder: tools/PROPFONT in the Windows XT repository.
