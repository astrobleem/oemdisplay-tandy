PCjr AND COLORPLUS SOFTWARE PANNING

JRPAN.ZIP is for IBM PCjr. CPPAN.ZIP is for Plantronics ColorPlus.
Each provides a 320x400 desktop through a 320x200, 16-color viewport.
Use an existing Windows 3.0 real-mode installation in C:\WINDOWS.

Extract the matching ZIP to C:\, exit Windows, and run C:\JRPAN\INSTALL
or C:\CPPAN\INSTALL. Choose Display, Other, that same folder, then the
320x400 software-panning entry. Start with JRSTART or CPWIN and run PANCFG
from Windows File > Run. The installer stages required files automatically.

To return to fixed mode: PANCFG OFF, exit Windows, run INSTALL again and
select the included 320x200 fixed entry. Existing startup programs are kept.
PCjr requires its DOS driver to reserve the video page; JRGUARD checks it.
Both downloads include their grabber, fonts, logos and helper programs. No manual checksums, file searches or INI editing needed.

These are software viewports. Emulator evidence covers DOSBox-X PCjr and
86Box XT/Plantronics with 640 KB; it does not establish physical hardware
qualification. The shadow uses 32,000 additional bytes over fixed mode.

Downloads and evidence:
https://github.com/astrobleem/oemdisplay-tandy/releases/tag/experimental-softpan-2026-10-24
https://github.com/astrobleem/oemdisplay-tandy/blob/main/docs/SOFTPAN/README.MD
