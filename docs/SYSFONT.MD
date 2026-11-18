# Graphics System fonts

These drivers-only packages revise the Windows **System** face used by menus,
titles and controls. They preserve all glyph advances, dialog metrics, extended
characters and Fixed/Terminal fonts. The approved nine-pixel M/W and I/J/C/E/S
spacing remain intact. Existing low-resolution dialog clipping can remain.

| Hardware | Driver source with revised System fonts |
| --- | --- |
| Tandy EX/HX; five fixed modes and shared panning paths | [SFTANDY.ZIP](https://github.com/astrobleem/oemdisplay-tandy/releases/download/windows-xt/SFTANDY.ZIP) |
| IBM CGA RGBI; fixed, compact and panning choices | [SFCGA.ZIP](https://github.com/astrobleem/oemdisplay-tandy/releases/download/windows-xt/SFCGA.ZIP) |
| IBM PCjr fixed/panning | [SFPCJR.ZIP](https://github.com/astrobleem/oemdisplay-tandy/releases/download/windows-xt/SFPCJR.ZIP) |
| Plantronics ColorPlus fixed/panning | [SFPCP.ZIP](https://github.com/astrobleem/oemdisplay-tandy/releases/download/windows-xt/SFPCP.ZIP) |
| Amstrad PC1512 | [SF1512.ZIP](https://github.com/astrobleem/oemdisplay-tandy/releases/download/windows-xt/SF1512.ZIP) |
| Tandy SL/2 Video II (candidate runtime unverified) | [SFTGA2.ZIP](https://github.com/astrobleem/oemdisplay-tandy/releases/download/windows-xt/SFTGA2.ZIP) |
| Olivetti PC1 / Yamaha B000h | [SFPC1.ZIP](https://github.com/astrobleem/oemdisplay-tandy/releases/download/windows-xt/SFPC1.ZIP) |
| Yamaha B800h | [SFYAMA.ZIP](https://github.com/astrobleem/oemdisplay-tandy/releases/download/windows-xt/SFYAMA.ZIP) |

Use an existing Windows 3.0 installation. Exit Windows, extract the matching
folder, run the hardware packet's normal memory guard where required, then run
Windows `SETUP` from DOS. Choose **Display → Other**, enter that extracted folder,
select your existing matching hardware/profile and **Complete Changes**. Give
the same folder again for the driver disk; give original Windows media for OS
disk requests. Cold-start with the packet's normal launcher/guard. See the
included `SYSFONT.TXT` and existing hardware instructions. No Python or new
installer is needed. Existing full-install archives remain available; use this
driver route afterward to activate the revised System face.

Tandy 320×200×16 uses twelve-row XTE; the other fixed Tandy modes and shared XTC
paths use eight-row XTC. CGA100 uses five-row CG1. Generic CGA OEM Setup standard
320/640 choices select **eight-row XTC**, and its compact choices select CG1.
The included six-row CG2 resource serves the existing dedicated 320 profile;
selecting generic 320 does not activate CG2. The existing descriptors and driver
binaries retain their behavior. PCjr/ColorPlus use their existing XTE choices;
PC1512, Video II and Yamaha paths retain XTC selection.

Native emulator checks covered font widths/pixels, menus/dialogs, cold starts,
ordinary Setup switching and shared panning paths. Video II's font selection and
package staging were checked, but its candidate runtime has **not** been tested
on a matching SL/2 fixture. PC1 checks establish logical Windows rendering, not
physical scanout. Physical hardware remains untested, and fonts do not fix or
diagnose PPC512 flicker. The separate PPCAB comparison is not included.

TEXT80/TXT40 retain their eight-pixel fixed-cell fonts. Proportional glyphs are
not supported by those presenters; these graphics packages do not change their
ROM text faces. Optional application fonts remain a separate choice.
