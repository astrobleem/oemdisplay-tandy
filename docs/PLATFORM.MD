# Other machine-specific video packages

These packages have separate install paths and qualification limits. A result for one card or computer does not qualify another.

| Target | Public download | Evidence, status and guide |
| --- | --- | --- |
| Tandy Video II, emulated SL/2 family | [TNDYV2.ZIP](https://github.com/astrobleem/oemdisplay-tandy/releases/download/experimental-video-ii-2026-10-14-r2/TNDYV2.ZIP) | Experimental; Windows rendering is for the SL/2 emulator profile only. Other SL/TL/RL models and physical hardware are unqualified. EX/HX must not use it. Run T2RESV before Setup and every Windows start; see [install/recovery](tga2/INSTALL.TXT) and the [qualification](https://github.com/astrobleem/oemdisplay-tandy/releases/tag/experimental-video-ii-2026-10-14-r2). |
| Amstrad PC1512 | [PC1512.ZIP](https://github.com/astrobleem/oemdisplay-tandy/releases/download/experimental-displays-2026-10-12/PC1512.ZIP) · [front door](https://github.com/astrobleem/windows-3-amstrad-pc1512) | Experimental emulator evidence; one cursor-state case remains unresolved. [Install/recover](../experiments/DISPLAY3/PC1512.TXT). |
| IBM PCjr | [PCJRSET.ZIP](https://raw.githubusercontent.com/astrobleem/oemdisplay-tandy/main/downloads/experimental/PCJR/PCJRSET.ZIP) · [front door](https://github.com/astrobleem/windows-3-pcjr) | 320×200×16 Setup packet; clean and existing-install Setup tested in DOSBox-X. This is a repository-file download, not a GitHub Release asset. [Install/recover](../downloads/experimental/PCJR/README.MD). |
| IBM XT + Plantronics ColorPlus | [PCP3216.ZIP](https://github.com/astrobleem/oemdisplay-tandy/releases/download/experimental-displays-2026-10-12/PCP3216.ZIP) · [front door](https://github.com/astrobleem/windows-3-plantronics) | Experimental emulator rendering; requires the ColorPlus card and its dedicated VRAM. [Install/recover](../experiments/DISPLAY3/PCP3216.TXT). |
| Olivetti Prodest PC1 / Yamaha V6355D | [PC1/B000 ZIP](https://raw.githubusercontent.com/astrobleem/oemdisplay-tandy/main/downloads/experimental/yamaha-candidate03/PC1-B000-CANDIDATE03.ZIP) · [Yamaha B800 ZIP](https://raw.githubusercontent.com/astrobleem/oemdisplay-tandy/main/downloads/experimental/yamaha-candidate03/YAMAHA-B800-CANDIDATE03.ZIP) · [front door](https://github.com/astrobleem/windows-3-olivetti-pc1) | Experimental repository files, not release assets. PC1/B000 has build and host checks only; no emulator, Setup or physical-PC1 test. The separate B800 screenshot is an 86Box IBM XT profile, not a PC1. [Corrected evidence](yamaha/QUALIFICATION.MD) · [guide](../experiments/YAMAHA/README.MD). |
| 80-column TEXT80 | [TEXT80.ZIP](https://raw.githubusercontent.com/astrobleem/oemdisplay-tandy/main/downloads/experimental/TEXT80/TEXT80.ZIP) · [front door](https://github.com/astrobleem/text-mode-windows) | Experimental text modes and compact C25; C25's recorded Windows binary passed 54/54 checks in 86Box XT/CGA. Other rebuilds have newer host audits, not fresh Windows GUI runs. [Install, rollback and exact scope](../downloads/experimental/TEXT80/README.MD). |

### PCjr clean-install evidence

<a href="https://github.com/astrobleem/oemdisplay-tandy/blob/613137d0029817b42e141a11685182d867da911d/docs/pcjr/INSTALL/DESKTOP.PNG"><img src="pcjr/INSTALL/DESKTOP.PNG" alt="Actual clean-install Windows 3.0 desktop on the emulated IBM PCjr at 320x200x16" width="480"></a>

*DOSBox-X · IBM PCjr · Windows 3.0 real mode · 320×200×16. PR #138 merged at [commit 613137d](https://github.com/astrobleem/oemdisplay-tandy/commit/613137d0029817b42e141a11685182d867da911d) after 40 host tests; the [26/26 clean-install session report](pcjr/INSTALL/SESSION.JSN) pins source commit [9ae4408](https://github.com/astrobleem/oemdisplay-tandy/commit/9ae44084127fe5d2f0c57ee1e1842d1ee1885573). The screenshot and PCJRSET.ZIP are repository evidence/downloads, not new release assets.*

<img src="yamaha/YAMAHA03.JPG" alt="Original 86Box screenshot of Windows 3.0 on an emulated IBM XT with a standalone Yamaha V6355D B800 profile at 160x200x16" width="480">

*86Box · IBM XT (1986), 8088 at 4.77 MHz · Windows 3.0 real mode · 160×200×16 B800 profile. This proves only the pictured emulator profile, not an Olivetti PC1 or physical hardware. [Qualification and source evidence](yamaha/QUALIFICATION.MD).*


[Back to Windows XT](../README.md)
