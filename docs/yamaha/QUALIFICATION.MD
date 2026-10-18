# Yamaha Candidate 03: evidence and qualification limits

This summary records the candidate results audited from the supplied evidence archive. The screenshot below is an original capture, not a generated image.

## B800 emulator screenshot

![Original 86Box screenshot of Windows 3.0 on an emulated IBM XT (1986) with a standalone Yamaha V6355D B800h profile at 160x200x16](YAMAHA03.JPG)

Source-built [86Box commit ceb009f](https://github.com/86Box/86Box/commit/ceb009f17daeecbb81e1ddf26ad63beda9300afe), IBM XT (1986), 8088 at 4.77 MHz, 640 KB, standalone Yamaha V6355D card, display_type 2 RGB333 at B800h. Windows 3.0 real mode, 160x200x16. This is emulator output for the B800 profile, not an Olivetti PC1 machine or hardware photograph.

## Saved test results

- **YAM160.DRV, B800h:** build PASS; 49 host semantic cases and 30 rejected staging mutations; 92 Windows real-mode cases; 2,944,000 pixel comparisons and 160,000 cursor-pixel comparisons; two exit/relaunch cycles.
- **PC1YAMA.DRV, B000h:** build PASS; 49 host semantic cases and 30 rejected staging mutations. No emulator, physical PC1, or Windows Setup test.
- The recorded B800 Windows Setup test used the original local packet with `CGA.GR2` and `CGALOGO.LGO` present. The public driver package is not available and no reduced package has been tested.

The source patch is based on public [upstream commit 212842c](https://github.com/astrobleem/oemdisplay-tandy/tree/212842cdd9c6877d8a01b00d8d6bc7e8e65f401a). The test archive records candidate commit `8c83dee0a3ae13a7d2b757ce3e14899afcd8e5db`, which is not present in public Git history. The source/evidence ZIP is not public. This publication did not rebuild the candidates or rerun an emulator.

## Limits

PC1/B000, physical monitor output, RGB/SCART behavior, and Windows 3.1 are unqualified. The B800 profile is a standalone emulator card configuration, not a complete Olivetti PC1 model. The two profiles use different display-memory apertures and cannot be interchanged; there is no hardware auto-detection. The original XT Pixels metrics remain and some 160-pixel dialogs can clip. No Windows or DOS media, ROM, compiler, or SDK is included.
