# Yamaha V6355D and Olivetti PC1: Candidate 03

Candidate 03 has two separate experimental Windows 3.0 real-mode display-driver profiles. No driver binary or source ZIP is currently published in the canonical repository or its GitHub Releases. The public record includes an original B800 emulator screenshot and a curated evidence summary.

| Profile | Mode and binary | Recorded status |
| --- | --- | --- |
| Olivetti Prodest PC1, B000h | PC1YAMA.DRV, 160x200x16, 54,992 bytes | Build PASS; 49 host semantic cases and 30 rejected staging mutations. No emulator, Windows Setup, or physical PC1 test. |
| Standalone Yamaha V6355D emulator profile, B800h | YAM160.DRV, 160x200x16, 55,008 bytes | Build PASS; 49 host semantic cases and 30 rejected staging mutations; 86Box Windows 3.0 evidence. This does not qualify PC1 hardware. |

[Original emulator screenshot](../../docs/yamaha/YAMAHA03.JPG) · [qualification and test summary](../../docs/yamaha/QUALIFICATION.MD).

## Expected install route and support files

The archived OEM Setup INF requires `CGA.GR2` and `CGALOGO.LGO`. They are Windows support files and are not included in any public package. If a package is published later, users must supply matching files from their own licensed Windows 3.0 installation/media. The original emulator Setup record used those local support inputs; no PC1 Setup run was made.

For a compatible profile, the recorded Setup route is to back up a working Windows 3.0 installation, use a disposable clone, run Windows Setup from DOS, choose **Display / Other**, select only the exact matching profile label, then start in real mode with `WIN /R`. Do not use the Tandy launcher or `RESERVE` helper.

There is no hardware auto-detection. The B000h PC1 and B800h emulator profiles are not interchangeable; choosing the wrong one can write to the wrong video-memory aperture.

## Evidence and limits

The B800 test used source-built [86Box commit ceb009f](https://github.com/86Box/86Box/commit/ceb009f17daeecbb81e1ddf26ad63beda9300afe), configured as IBM XT (1986), 8088/4.77 MHz, 640 KB, standalone Yamaha V6355D display_type 2 RGB333 at B800h. The guest was Windows 3.0 real mode, 160x200x16. The saved run passed 92 Windows cases, comparing 2,944,000 pixels and 160,000 additional cursor pixels, plus two clean exit/relaunch cycles. It was not a full PC1 machine.

The source patch is based on public [upstream commit 212842c](https://github.com/astrobleem/oemdisplay-tandy/tree/212842cdd9c6877d8a01b00d8d6bc7e8e65f401a). The candidate-source commit recorded by the test archive is `8c83dee0a3ae13a7d2b757ce3e14899afcd8e5db`; it is not present in public Git history. The source/evidence archive remains unpublished, so this page summarizes saved run records and links the public emulator commit. No drivers were rebuilt and no emulator was run for this documentation update.

Physical PC1, monitor centering, RGB/SCART behavior, and Windows 3.1 are unqualified. The original XT Pixels metrics remain and some 160-pixel dialogs can clip. No Windows/DOS media, ROMs, compiler, or SDK are included.
