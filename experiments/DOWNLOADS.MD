# Windows XT tested experiments - 7 October 2026

These public downloads expose newer qualified work separately from the Windows XT 0.1.0-rc.1 baseline. No review queue gates these assets. The baseline remains recommended for a fresh installation; the latest experimental display overlay is TRIAL7 combined, and the latest qualified Tandinator game here is TANDI11/app 0.3.8. All are experimental, with emulator evidence and the specific physical limits below.

## Choose a download

| Component | Download | Recommended use / limits |
| --- | --- | --- |
| Fresh install baseline | [Windows XT 0.1.0-rc.1](https://github.com/astrobleem/oemdisplay-tandy/releases/tag/v0.1.0-rc.1) | Standard 720 KB disk, TR5 graphics, Tandy Start 14. Reuses your own matching Windows 3.0 files. |
| Latest qualified display optimization | [TRIAL7.ZIP](https://github.com/astrobleem/oemdisplay-tandy/releases/download/experiments-2026-10-07/TRIAL7.ZIP) + [SOURCEQA.ZIP](https://github.com/astrobleem/oemdisplay-tandy/releases/download/experiments-2026-10-07/SOURCEQA.ZIP) | Combined retained TR6 DIB + border/line + short raster-label optimization, five graphics profiles. One-shot overlay on an exact already-active TR5 installation. |
| Latest qualified shell review fixes | [TSFIX01.ZIP](https://github.com/astrobleem/oemdisplay-tandy/releases/download/experiments-2026-10-07/TSFIX01.ZIP) | PIF selection, shutdown-query and mnemonic fixes. Test as a secondary shell in a disposable Program Manager guest; primary-shell lifecycle was not fully rerun. |
| Alternate app/Run UI polish | [APPUI01.ZIP](https://github.com/astrobleem/oemdisplay-tandy/releases/download/experiments-2026-10-07/APPUI01.ZIP) | Seven apps with clearer feedback and separate friendlier TSHELL Run wording. This is not combined with TSFIX01. |
| Latest qualified Tandinator game | [TANDI11.ZIP](https://github.com/astrobleem/oemdisplay-tandy/releases/download/experiments-2026-10-07/TANDI11.ZIP) | App 0.3.8: prompt/cap/F3 fixes, original artwork/demo, optional notebook OFF every launch, explicit Ask Two never beyond 40 questions. |
| Separate fourth-saver shell option | [TANDI10.ZIP](https://github.com/astrobleem/oemdisplay-tandy/releases/download/experiments-2026-10-07/TANDI10.ZIP) | App 0.3.7 is superseded by 0.3.8 for game play; this packet retains the separately tested TSHELL fourth-saver integration. Not an installed-shell upgrade. |
| Keyboard first-party tools/source | [K3TOOLS.ZIP](https://github.com/astrobleem/oemdisplay-tandy/releases/download/experiments-2026-10-07/K3TOOLS.ZIP) | RAWKEY, WINKEY, K3SET and adaptation/build source. Microsoft-derived TNDYK3.DRV is excluded because its notice leaves redistribution rights unresolved. Read READFIRST.TXT. |
| Latest serial diagnostic/helper polish | [UTILDOS1.ZIP](https://github.com/astrobleem/oemdisplay-tandy/releases/download/experiments-2026-10-07/UTILDOS1.ZIP) | WHEEL DOS diagnostic and splash status helper, with original guards, matching source and recorded host/native evidence. This is not a Windows mouse/scrolling driver. |
| Host learning research | [LEARN11.ZIP](https://github.com/astrobleem/oemdisplay-tandy/releases/download/experiments-2026-10-07/LEARN11.ZIP), [LEARN12.ZIP](https://github.com/astrobleem/oemdisplay-tandy/releases/download/experiments-2026-10-07/LEARN12.ZIP) | Offline host studies/UI prototypes, not native apps. UNKNOWN answers are scripted assumptions, not audited facts; learned reports can hurt accuracy. |

Checksums for every asset are in [SHA256SUMS](https://github.com/astrobleem/oemdisplay-tandy/releases/download/experiments-2026-10-07/SHA256SUMS). [INVENTORY.JSON](https://github.com/astrobleem/oemdisplay-tandy/releases/download/experiments-2026-10-07/INVENTORY.JSON) records exact asset/source identities and all pending items. Source, tests and recorded native evidence are inside the corresponding archive, except TRIAL7's full source/evidence is in SOURCEQA.ZIP. Original checkpoint descriptions such as "private", "not published" and old publication flags are preserved historical metadata, not the current access status.

## TRIAL7 exact choices

The shipped runtime is the qualified **combined** variant; no isolated border-only or text-only install kit is substituted for it. SOURCEQA.ZIP preserves the source and all 15 mode/variant build/audit records for border-only, text-only and combined benchmarking. The older TR6 DIB path is included in combined; it is not a new standalone TR6 package.

| Active mode/code | Shipped driver | SHA256 |
| --- | --- | --- |
| 160x200x16 / 16016 | TR51616.DRV | `a01891505d8acf64d1473076ad05d1a6760d4e0f70bbd074edd6a7c911255e0e` |
| 320x200x16 / 32016 | TR53216.DRV | `f922f12168de69ec2f8a761ce7fce2cbe2080b9e3fcfb06e3a3dac4faba6d502` |
| 320x200x4 / 3204 | TR53204.DRV | `bc2e1ee14f52e1b71732018facd030ba075bb18ce63cabee05f2110e830366e8` |
| 640x200x4 / 6404 | TR56404.DRV | `ce49766434a3c628fdee00aa1fb6e8a79aa3a22f9996c9dc202a5a2d313127cc` |
| 640x200x2 / 6402 | TR56402.DRV | `fce1790a0fcba793f759d67d38117360818a83e716ffe2126519f6d82ea3358f` |

Use C:\WINXT with Windows at C:\WINDOWS and the exact supported helpers. Back up storage and retain a plain-DOS recovery route. Exit Windows. Extract the whole runtime to C:\TRIAL7. For the CURRENT active 640x200x4 mode, run `APPLY 6404 YES`; use the matching code above for another active mode. Wait for APPLY VERIFIED, then use the existing guarded C:\WINXT\WINXT launcher. Do not use Setup to switch modes while applied. To roll back from plain DOS use `RESTORE 6404 YES` with the same code and wait for verification. Restore an existing TR6 overlay through its own original kit first. Read the complete runtime README before use; do not bypass identity checks, delete markers or reuse backups for another mode.

TRIAL7 recorded qualification: 1,800 border/text differential cases, 580 DIB cases, 14,144,000 direct-line pixels, 10 native Windows sessions, 143 host rollback cases and 76 DOS rollback cases. All five selected binaries pass emitted-8086 audits. Fixed-cycle benchmark results are not calibrated physical-8088 speedups. Original EX/HX four-color mode caveats, physical storage/power-loss behavior, unsupported fonts/ROPs and long soaks remain outside scope.

## Safe use of app and shell experiments

Extract to new folders and close older loaded instances. TSFIX01, APPUI01's shell and TANDI10's fourth-saver shell must be tried separately in disposable Program Manager guests, retaining matching TSINPUT.DLL. Separate folders do not isolate loaded Win16 module names or Windows-directory TSHELL.INI. Preserve configuration/snapshot first; close and discard the guest/snapshot to undo. No experiment here automatically installs, replaces or selects the shell.

For TANDI11 use its RUN directory together, retain the standard DAT and guarded display launcher. Learning defaults OFF each launch. Reports require identity/review/save; AUDIT08 remains a separate unpromoted option with a recorded noisy-answer regression. F3 preference is saved by ordinary manual play; demo/saver operation does not save learning/settings. No robotic ah-ha voice is present in these qualified app bytes; its separate integration is pending. New-character learning and a contributed-overlay merge tool are also pending, not hidden implemented features.

TSFIX01 has 155 recorded native checks; APPUI01 has 41 accepted native runs/2,663 checks. TANDI10 and TANDI11 each retain 19 native runs; TANDI11 also retains 226 notebook checks, nine settings checks and 30,720 deterministic roster games. This publication rechecks exact archives/source/runtime/evidence. It does not assert new emulator runs, real-hardware acceptance or primary-shell coverage beyond the packets' documented scope.

## Input driver status and missing builds

The keyboard candidate is already public in the repository as src/tandyk3/TNDYK3.DRV with K3SET, but its NOTICE.TXT does not assert Microsoft-derived runtime redistribution permission. This release therefore distributes first-party tools/adaptation source only. K3SET APPLY requires the separately authorized exact driver. Physical evidence covers 17 raw press/release pairs; Windows translation, modifier combinations, typematic and Hold-to-Start remain physically unqualified.

WHEEL has two bounded physical Tandy EX/Genius NetScroll raw captures. It observes DOS/serial wheel packets and does not implement Windows scrolling. The newer diagnostic summary build has recorded native and mock tests, not a new physical-driver qualification. Existing Windows input drivers are retained by the baseline release.

**TRIAL8 and TPDRV03:** no verified source/runtime packet, test identity or public PR was found in current main or the accessible local workspaces. They are explicitly unresolved inventory items. They cannot be relabeled from TRIAL7 or WHEEL, manufactured, or represented as published tested drivers. A source owner must provide the exact packet/qualification/redistribution record before those particular downloads can be added.

## Other newer qualified desktop/app work

These are also public downloads, rather than PR-only artifacts:

- [VISPART1.ZIP](https://github.com/astrobleem/oemdisplay-tandy/releases/download/experiments-2026-10-07/VISPART1.ZIP): Matrix low-color fallback polish and rounder XTEyes pupil travel, matching source/evidence.
- [VISPART2.ZIP](https://github.com/astrobleem/oemdisplay-tandy/releases/download/experiments-2026-10-07/VISPART2.ZIP): Maze sliced first-frame setup and Starfield overlap repair; includes the tested Arwing02 laser-repair variant. The measured Slosh edge proposal was rejected and is not shipped.
- [ARWING02.ZIP](https://github.com/astrobleem/oemdisplay-tandy/releases/download/experiments-2026-10-07/ARWING02.ZIP): original optional Starfield flight mode with the qualified horizon/laser correction and its matching optional shell. [ARWING01.ZIP](https://github.com/astrobleem/oemdisplay-tandy/releases/download/experiments-2026-10-07/ARWING01.ZIP) is the historical first version. These alternatives are not silently combined with TSFIX01 or the fourth-saver shell.
- [UTILGUI1.ZIP](https://github.com/astrobleem/oemdisplay-tandy/releases/download/experiments-2026-10-07/UTILGUI1.ZIP): EXJOY, FileDrop and Dialogs status polish, source and 26 recorded qualified cases/30 native screenshots. The unchanged app-local COMMDLG.DLL is the project's first-party compatibility implementation, not a Microsoft DLL. Follow each fixed fixture/new scratch-file workflow; no installed OS component is replaced.

Experimental hardware text is already the unchanged sixth profile in the baseline. Its source/proof is public under experiments/TEXTMODE; no newer text build was found. TRIAL4 is older than TR5 and retained as historical evidence. Standalone app examples remain public source/runtime in the repository; the newer packets above cover all named current experiments beyond the baseline in this checkout.

## Older qualified Tandinator checkpoints

These are public historical comparisons, not recommended over 0.3.8: [TANDI03](https://github.com/astrobleem/oemdisplay-tandy/releases/download/experiments-2026-10-07/TANDI03.ZIP), [TANDI04](https://github.com/astrobleem/oemdisplay-tandy/releases/download/experiments-2026-10-07/TANDI04.ZIP), [TANDI05](https://github.com/astrobleem/oemdisplay-tandy/releases/download/experiments-2026-10-07/TANDI05.ZIP), [TANDI07](https://github.com/astrobleem/oemdisplay-tandy/releases/download/experiments-2026-10-07/TANDI07.ZIP), [TANDI08](https://github.com/astrobleem/oemdisplay-tandy/releases/download/experiments-2026-10-07/TANDI08.ZIP), [TANDI09](https://github.com/astrobleem/oemdisplay-tandy/releases/download/experiments-2026-10-07/TANDI09.ZIP). The standard data is retained where documented; AUDIT08 is optional and its known noisy-input regression is disclosed. Earlier canonical TANDI02 remains in examples/TANDINAT. TRIAL4 and older display checkpoints remain historical repository evidence; they are older than the release's TR5 baseline.

## Provenance and publication scope

The baseline source revision is a17883908dce8d780d4b1b4b3581cafd695d8d14. This experiments tag additionally publishes the immutable locally qualified TANDI10 and host-study packets, generated first-party input-tools/diagnostic ZIPs, exact hash records and read-only verification. It changes no program bytes or canonical/runtime defaults. Repository/source links are pinned to the release tag. Existing first-party and third-party source notices remain authoritative; publication does not grant new rights to Microsoft code/media.

No Windows/DOS media, support fonts, WIN.COM, compiler/DDK binaries, guest installations, user reports or credentials are included. Use your own licensed inputs to rebuild/reproduce native tests. No actual installation, CF write or silent default promotion was performed. The older draft and baseline public prerelease remain intact.
