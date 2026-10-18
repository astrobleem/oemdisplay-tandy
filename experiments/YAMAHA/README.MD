# Yamaha V6355D and Olivetti PC1: Candidate 03

Candidate 03 contains two separate experimental Windows 3.0 real-mode display-driver profiles. The ZIPs below are repository-file downloads, not GitHub Release assets. They are experimental packages, not installers.

| Profile | Download | Recorded status |
| --- | --- | --- |
| Olivetti Prodest PC1, B000h | [PC1/B000 candidate ZIP](https://raw.githubusercontent.com/astrobleem/oemdisplay-tandy/main/downloads/experimental/yamaha-candidate03/PC1-B000-CANDIDATE03.ZIP) — 37,598 bytes; SHA-256 `bf68e988bd309daee667d65d3534b5ad42c1c9b79c0aaa99e25d4527743b2104` | `PC1YAMA.DRV`, 160x200x16; build PASS and 49 host semantic cases. No emulator, Windows Setup, or physical PC1 test. |
| Standalone Yamaha V6355D emulator profile, B800h | [B800 emulator candidate ZIP](https://raw.githubusercontent.com/astrobleem/oemdisplay-tandy/main/downloads/experimental/yamaha-candidate03/YAMAHA-B800-CANDIDATE03.ZIP) — 37,607 bytes; SHA-256 `57e65dd45943294ecc2d227c259d9d813fca61585f39c2171aff9dff2e6f09f0` | `YAM160.DRV`, 160x200x16; build PASS and 49 host semantic cases. Separate DOSBox-X raw-VRAM/API results and 86Box screenshot; no PC1 hardware qualification. |
| Source and evidence | [Candidate 03 source/evidence ZIP](https://raw.githubusercontent.com/astrobleem/oemdisplay-tandy/main/downloads/experimental/yamaha-candidate03/YAMAHA-CANDIDATE03-SOURCE-EVIDENCE.ZIP) — 209,499 bytes; SHA-256 `cc140d2082c8fa07ccaffc3581e235d1344679eefb97018cd7db6988c962cabf` | Source patch, test reports and original screenshots. Recorded candidate source commit is not present in public Git history. |

[Original B800 86Box screenshot](../../docs/yamaha/YAMAHA03.JPG) · [corrected qualification summary](../../docs/yamaha/QUALIFICATION.MD) · [canonical development repository](https://github.com/astrobleem/oemdisplay-tandy).

## Evidence and limits

The 92-case Windows real-mode/API suite, 2,944,000 pixel comparisons and 160,000 cursor-pixel comparisons are recorded in the source archive's `EVIDENCE/WINDOWS.JSN`. That report specifies a DOSBox-X raw-VRAM/API contract; DOSBox-X does not emulate Yamaha scanout. The separate actual 86Box screenshot record is `EVIDENCE/SCANOUT.JSN`, for a Windows 3.0 guest on an emulated IBM XT (1986), 8088/4.77 MHz, 640 KB, with a standalone Yamaha V6355D at B800h. It is not a PC1 test.

The source archive's `README.TXT`, `EVIDENCE/QUALIFY.JSN` and `EVIDENCE/TESTSUMMARY.TXT` retain an earlier summary that associates the 92-case suite with 86Box. The underlying `EVIDENCE/WINDOWS.JSN` identifies the suite as DOSBox-X, while `EVIDENCE/SCANOUT.JSN` records the separate 86Box screenshot. The corrected qualification summary linked above makes this distinction explicit.

`PC1YAMA.DRV` targets segment B000h; `YAM160.DRV` targets B800h. These profiles are not interchangeable and have no hardware auto-detection. The PC1/B000 reports record build and host checks only; runtime, Setup and physical PC1 remain untested. The B800 screenshot is emulator evidence, not hardware qualification. Physical RGB/SCART behavior and PC1 hardware are unqualified. Some 160-pixel dialogs can clip.

## Setup route and support files

Both Setup INFs require matching `CGA.GR2` and `CGALOGO.LGO` files. They are intentionally omitted; supply them from your own licensed Windows 3.0 installation/media. Back up the installation and use a disposable clone. From DOS, run Windows Setup, choose **Display / Other**, select only the exact profile label, then start Windows in real mode with `WIN /R`. Do not use the Tandy launcher or `RESERVE` helper.

The recorded B800 selector test used the original local packet and those support files. The reduced public B800 package was not retested end-to-end; PC1/B000 Setup was not tested. Follow each ZIP's README and use only the matching target profile. No Windows/DOS media, ROM, compiler, or SDK is included. No candidate was rebuilt or emulator rerun for this documentation update.
