# Yamaha V6355D and Olivetti PC1: Candidate 03

Candidate 03 contains two separate experimental Windows 3.0 real-mode display-driver profiles. The ZIPs below are repository-file downloads, not GitHub Release assets. They are experimental packages, not installers.

| Profile | Download | Recorded status |
| --- | --- | --- |
| Olivetti Prodest PC1, B000h | [PC1/B000 candidate ZIP](https://raw.githubusercontent.com/astrobleem/oemdisplay-tandy/main/downloads/experimental/yamaha-candidate03/PC1-B000-CANDIDATE03.ZIP) — 37,647 bytes; SHA-256 `a8e4e5268c46bf8971ae0cf224e6145aff2de2e35eeb9812d04aaa6f42bfb56f` | `PC1YAMA.DRV`, 160x200x16; build PASS and 49 host semantic cases. No emulator, Windows Setup, or physical PC1 test. |
| Standalone Yamaha V6355D emulator profile, B800h | [B800 emulator candidate ZIP](https://raw.githubusercontent.com/astrobleem/oemdisplay-tandy/main/downloads/experimental/yamaha-candidate03/YAMAHA-B800-CANDIDATE03.ZIP) — 37,663 bytes; SHA-256 `6e1353dde1442202e2604af881a0e0fc2ea81c9bafbe9c24bd495328ce41b62e` | `YAM160.DRV`, 160x200x16; build PASS and 49 host semantic cases. Separate DOSBox-X raw-VRAM/API results and 86Box screenshot; no PC1 hardware qualification. |
| Source and evidence | [Candidate 03 source/evidence ZIP](https://raw.githubusercontent.com/astrobleem/oemdisplay-tandy/main/downloads/experimental/yamaha-candidate03/YAMAHA-CANDIDATE03-SOURCE-EVIDENCE.ZIP) — 212,392 bytes; SHA-256 `8e74257037af8dd5ac40d02ea6482c3d990814ebb1bd38552e713d310e32b1e5` | Source patch, corrected DOSBox-X and 86Box reports, and original screenshots. Recorded candidate source commit is not present in public Git history. |

[Original B800 86Box screenshot](../../docs/yamaha/YAMAHA03.JPG) · [corrected qualification summary](../../docs/yamaha/QUALIFICATION.MD) · [canonical development repository](https://github.com/astrobleem/oemdisplay-tandy).

## Evidence and limits

The source/evidence ZIP includes `EVIDENCE/WINDOWS.JSN`, which records the 92-case DOSBox-X raw-VRAM and Windows real-mode API/memory contract. DOSBox-X does not emulate Yamaha scanout. `EVIDENCE/SCANOUT.JSN` records the separate 86Box Windows 3.0 guest screenshot for an emulated IBM XT (1986), 8088/4.77 MHz, 640 KB, with a standalone Yamaha V6355D at B800h. This screenshot is emulator evidence, not a PC1 test or physical hardware qualification.

The archive's `README.TXT`, `EVIDENCE/QUALIFY.JSN`, and `EVIDENCE/TESTSUMMARY.TXT` distinguish the DOSBox-X contract report from the separate 86Box screenshot record. The source patch is based on public upstream commit 212842cdd9c6877d8a01b00d8d6bc7e8e65f401a; the recorded candidate source commit is not in public Git history.

`PC1YAMA.DRV` targets segment B000h; `YAM160.DRV` targets B800h. These profiles are not interchangeable and have no hardware auto-detection. The PC1/B000 reports record build and host checks only; runtime, Setup and physical PC1 remain untested. The B800 screenshot is emulator evidence, not hardware qualification. Physical RGB/SCART behavior and PC1 hardware are unqualified. Some 160-pixel dialogs can clip.

## Setup route and support files

Both Setup INFs require matching `CGA.GR2` and `CGALOGO.LGO` files. They are intentionally omitted; supply them from your own licensed Windows 3.0 installation/media. Back up the installation and use a disposable clone. From DOS, run Windows Setup, choose **Display / Other**, select only the exact profile label, then start Windows in real mode with `WIN /R`. Do not use the Tandy launcher or `RESERVE` helper.

The recorded B800 selector test used the original local packet and those support files. The reduced public B800 package was not retested end-to-end; PC1/B000 Setup was not tested. Follow each ZIP's README and use only the matching target profile. No Windows/DOS media, ROM, compiler, or SDK is included. No candidate was rebuilt or emulator rerun for this documentation update.
