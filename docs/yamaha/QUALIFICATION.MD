# Yamaha Candidate 03: evidence and qualification limits

This summary records the candidate results audited from the published source/evidence archive. The screenshot below is an original capture, not a generated image.

## B800 emulator screenshot

![Original 86Box screenshot of Windows 3.0 on an emulated IBM XT (1986) with a standalone Yamaha V6355D B800h profile at 160x200x16](YAMAHA03.JPG)

Source-built [86Box commit ceb009f](https://github.com/86Box/86Box/commit/ceb009f17daeecbb81e1ddf26ad63beda9300afe), IBM XT (1986), 8088 at 4.77 MHz, 640 KB, standalone Yamaha V6355D card, display_type 2 RGB333 at B800h. Windows 3.0 real mode, 160x200x16. This is emulator output for the B800 profile, not an Olivetti PC1 machine or hardware photograph.

## Public Candidate 03 files

These are experimental repository-file downloads, not GitHub Release assets or installers. The current Release inventory contains no Yamaha Candidate 03 assets.

| Artifact | Public download | Size and SHA-256 |
| --- | --- | --- |
| Olivetti Prodest PC1, B000h profile | [PC1/B000 candidate ZIP](https://raw.githubusercontent.com/astrobleem/oemdisplay-tandy/main/downloads/experimental/yamaha-candidate03/PC1-B000-CANDIDATE03.ZIP) | 37,647 bytes; `a8e4e5268c46bf8971ae0cf224e6145aff2de2e35eeb9812d04aaa6f42bfb56f` |
| Standalone Yamaha V6355D emulator profile, B800h | [B800 emulator candidate ZIP](https://raw.githubusercontent.com/astrobleem/oemdisplay-tandy/main/downloads/experimental/yamaha-candidate03/YAMAHA-B800-CANDIDATE03.ZIP) | 37,663 bytes; `6e1353dde1442202e2604af881a0e0fc2ea81c9bafbe9c24bd495328ce41b62e` |
| Source and evidence | [Candidate 03 source/evidence ZIP](https://raw.githubusercontent.com/astrobleem/oemdisplay-tandy/main/downloads/experimental/yamaha-candidate03/YAMAHA-CANDIDATE03-SOURCE-EVIDENCE.ZIP) | 212,392 bytes; `8e74257037af8dd5ac40d02ea6482c3d990814ebb1bd38552e713d310e32b1e5` |

The source/evidence archive includes `EVIDENCE/WINDOWS.JSN` for the DOSBox-X raw-VRAM/API contract and `EVIDENCE/SCANOUT.JSN` for the separate 86Box screenshot observation. It includes first-party source and original evidence images, but no Windows or DOS media, ROM, compiler, or SDK.

## Saved test results

- **YAM160.DRV, B800h:** build PASS (`EVIDENCE/B800BLD.JSN`); 49 host semantic cases and 30 rejected staging mutations (`EVIDENCE/B800HOST.JSN`). The host report covers models and selected-source interpretation only; it did not execute machine code, BIOS, Windows, an emulator, or hardware.
- **B800 DOSBox-X contract test:** `EVIDENCE/WINDOWS.JSN` records 92 Windows real-mode/API/memory cases, 2,944,000 pixel comparisons, 160,000 additional cursor-visible pixel comparisons, and two exit/relaunch cycles. Its scope is DOSBox-X raw VRAM and the Windows API/memory contract. DOSBox-X provides no Yamaha scanout emulation, so this is not B800 hardware scanout evidence.
- **B800 86Box screenshot:** `EVIDENCE/SCANOUT.JSN` records the separate Windows 3.0 guest screenshot shown above (`PALETTE.JPG`, 160x200 logical size). This is the 86Box scanout observation; it is separate from the 92-case DOSBox-X report and is not a PC1 test.
- **PC1YAMA.DRV, B000h:** build PASS (`EVIDENCE/PC1BUILD.JSN`); 49 host semantic cases and 30 rejected staging mutations (`EVIDENCE/PC1HOST.JSN`). The reports mark runtime and physical PC1 `NOT_TESTED`; there was no emulator, physical PC1, or Windows Setup test.
- **B800 Setup selector:** `EVIDENCE/OEMSETUP.JSN` records a Windows 3 DOS Setup Change Display/Other selection for the B800 emulator-only label. It used the original local packet with `CGA.GR2` and `CGALOGO.LGO` present. Those support files are omitted from the public profile package, which was not retested end-to-end. PC1/B000 installation and runtime were not tested.

The source patch is based on public [upstream commit 212842c](https://github.com/astrobleem/oemdisplay-tandy/tree/212842cdd9c6877d8a01b00d8d6bc7e8e65f401a). The test archive records candidate commit `8c83dee0a3ae13a7d2b757ce3e14899afcd8e5db`, which is not present in public Git history. This publication did not rebuild the candidates or rerun an emulator.

## Limits

PC1/B000, physical monitor output, RGB/SCART behavior, and Windows 3.1 are unqualified. The B800 profile is a standalone emulator card configuration, not a complete Olivetti PC1 model. The two profiles use different display-memory apertures and cannot be interchanged; there is no hardware auto-detection. The original XT Pixels metrics remain and some 160-pixel dialogs can clip. No Windows or DOS media, ROM, compiler, or SDK is included.
