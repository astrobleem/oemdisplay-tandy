# Graphics System fonts

These drivers-only packages revise the Windows **System** face used by menus,
titles and controls. Each font resource preserves its own advances, metadata
and extended coverage; Fixed/Terminal faces are retained. The source CGA 320
default now selects separate six-row UI6 and compact controls, so that selection
changes UI metrics compared with the former large profile. The approved nine-pixel M/W and I/J/C/E/S
spacing remain intact. Existing low-resolution dialog clipping can remain.

> Feature-branch checkpoint: the download links below still serve the prior
> release packages. The new 320 default requires rebuilt CGA/SFCGA packages;
> see [the UI checkpoint](../tools/RESUI/README.MD).

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
folder to the location required by its existing launcher: Tandy under
`C:\SFONTS\WINXT` (preserving any installed `C:\WINXT`), PCjr at `C:\JRPAN`,
ColorPlus at `C:\CPPAN`, and Video II at `C:\T2EXP`. Other driver source folders
can use their normal hardware-guide location. Run the packet's normal memory
guard where required, then run
Windows `SETUP` from DOS. Choose **Display → Other**, enter that extracted folder,
select your existing matching hardware/profile and **Complete Changes**. Give
the same folder again for the driver disk; give original Windows media for OS
disk requests. For Tandy EX/HX, start from the extracted driver folder with
`CD \SFONTS\WINXT` then `DISPWIN C: \WINDOWS` (use your actual paths).
This existing driver entry performs the required reservation and grabber/panning
preparation. The legacy full-install `STARTXT`/`FIXXT` route manages its original
font set, so use `DISPWIN` for this driver-only installation. Other hardware uses
its matching driver launcher/guard; respect every reservation failure. See the
included `SYSFONT.TXT` and existing hardware instructions. No Python or new
installer is needed. Existing full-install archives remain available.

The released packages retain their original profile selections: XTE for
Tandy 320x200x16 and PCjr/ColorPlus; XTC for the other broad graphics paths;
CG1/CG2 for compact CGA. The feature-branch OEM producer now selects by
physical viewport: CG1 at 160 pixels, separate hand-tuned six-row UI6 at
320 pixels, and corrected XTC at 640 pixels. Low viewports select existing
4x6 Fixed/Terminal companions so Windows 3.0 dialogs also scale appropriately;
the font bytes and deliberate monospace behavior are preserved. Graphics
OEM chrome changes while rendering segments, fixups, aspect, palettes and
memory guards remain exact. HPXY retains its already compact accepted driver
identity for its normal guarded launcher. The ordinary CGA 320 and 320C
paths agree, while 320L explicitly retains the legacy large option.
See [the current measured limits](../tools/RESUI/README.MD), including
remaining 160-pixel application-dialog overflow and text-mode rendering gaps.

Native emulator checks covered font widths/pixels, menus/dialogs, cold starts,
ordinary Setup switching and shared panning paths. Video II's font selection and
package staging were checked, but its candidate runtime has **not** been tested
on a matching SL/2 fixture. PC1 checks establish logical Windows rendering, not
physical scanout. Physical hardware remains untested, and fonts do not fix or
diagnose PPC512 flicker. The separate PPCAB comparison is not included.

TEXT80/TXT40 remain an open requirement. Their selected System face still
has eight-pixel fixed advances, and the current cell presenters cannot render
arbitrary proportional glyph pixels exactly. This checkpoint does not change
their defaults, implement an exact pixel fallback, or mark them complete or
exempt. Deliberate monospace application/Terminal faces are a separate role.
