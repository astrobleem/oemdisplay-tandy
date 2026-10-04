# README screenshot provenance

These are actual emulator captures: historical repository and TSTART08
frames are copied byte for byte, and the two TSTART09 frames come from the
new popup verification. No redraw, retouching, photo or generated mockup is
added. Native framebuffer decoding and emulator row/column duplication are
identified below. Capture content was visually inspected. Guest DOS example
paths are not host user paths.

Source revision: `f98a0ba99dfa006fb34466d3618c2afae8e5a066`.

| Asset | Original source | Scope |
| --- | --- | --- |
| [SETUP.PNG](SETUP.PNG) | [docs/modes/oem/CHOICES.PNG](../../docs/modes/oem/CHOICES.PNG) | Windows Setup choices; historical OEM package, not current trial selection. |
| [BOOT.PNG](BOOT.PNG) | [docs/splash/BOOT.PNG](../../docs/splash/BOOT.PNG) | Native custom splash; historical splash/OEM checkpoint. |
| [START.PNG](START.PNG) | [examples/TSHELL/EVIDENCE/CAPTURES/MENUBASE.PNG](../../examples/TSHELL/EVIDENCE/CAPTURES/MENUBASE.PNG) | Native framebuffer decoded by committed helper; historical menu, not current Programs/System/date editor. |
| [COOKIE.PNG](COOKIE.PNG) | [examples/COOKIE/EVIDENCE/baseline/GAME.PNG](../../examples/COOKIE/EVIDENCE/baseline/GAME.PNG) | Native 320x200x16 game capture. |
| [PINBALL.PNG](PINBALL.PNG) | [examples/PINBALL/EVIDENCE/6404/FINAL.PNG](../../examples/PINBALL/EVIDENCE/6404/FINAL.PNG) | Native logical 640x200x4; 640x400 PNG with row duplication. |
| [MATRIX.PNG](MATRIX.PNG) | [examples/MATRIX/EVIDENCE/MBASE.PNG](../../examples/MATRIX/EVIDENCE/MBASE.PNG) | Historical on-demand 320x200x16 capture, not automatic idle /S evidence. |
| [SLOSH.PNG](SLOSH.PNG) | [examples/SLOSH/EVIDENCE/160/MOTION.PNG](../../examples/SLOSH/EVIDENCE/160/MOTION.PNG) | Logical 160x200x16, horizontally duplicated to 320x200 by capture path. |
| [MAZE.PNG](MAZE.PNG) | [examples/MAZE/EVIDENCE/MAZE.PNG](../../examples/MAZE/EVIDENCE/MAZE.PNG) | Native windowed experimental framebuffer; not screensaver or hardware performance evidence. |
| [SOLITAIR.PNG](SOLITAIR.PNG) | [docs/modes/6404rg/SOLITAIR.PNG](../../docs/modes/6404rg/SOLITAIR.PNG) | Current red/green four-color profile; logical 640x200, rows doubled; startup/layout only, not a full game. |

Source evidence: [Setup/OEM results](../modes/oem/RESULT.JSON), [Solitaire capture record](../modes/6404rg/CAPTURE.JSON), [splash record](../SPLASH.MD), [TSHELL capture notes](../../examples/TSHELL/EVIDENCE/CAPTURES/README.TXT), and each app's README/TESTS evidence.

The pictures establish only the pictured UI state, not audio, complete
application coverage, physical hardware, unpictured updates or timing.
Historical frames retain their original scope. Stock Windows applications
shown in captures are compatibility examples; their binaries are not included.

## SHA-256 identities

The source and copied PNG hashes match exactly:

```text
7bfe37b657e8507192688ff5c63f3904472bda7e08aeac8ed7bb62c0c9d6408a  SETUP.PNG
2c0c668435e3fab7ecc3a4369911ddd642fdeb2d403c7f81e701b631a2c68f29  BOOT.PNG
44b37d4ccc82f350e210108da5ae3605332504c6a64bfde8de158633c50068ac  START.PNG
8ab6d7f127b96a8cd86b8cb609c570b82464d152845cfba08ed8a2f5afc4ae31  COOKIE.PNG
ddde65ce9e7e513bb8282afd3bb8db1108382814e3a22fe5b017fdfe422ff7fd  PINBALL.PNG
ec544bf5aba64ab508c92a60b70c00185c762c14a0d717b265ec0324b7b4dddc  MATRIX.PNG
a14f1649803047fb6a442f543d0698558cdae699f2ac8cab19ee2ca004aa4c15  SLOSH.PNG
19c5ecd391194016d83aeebf090bcc6821b8a8e96b15a9e7e4c50560179af763  MAZE.PNG
2a46f4f6b25c38f4eb74f6846f6b8f7aee700ff952c9fb6078174b76dbeb749e  SOLITAIR.PNG
```

## Tandy Start 08 captures

The following frames are byte-identical to the delivered TSTART08 package's
SOURCE.ZIP. Matching source is included in this branch; these retained 08 frames
keep their original build identity. Package
SHA-256: `8a400c880074b15410d133993ebd057d0c6ab819a6ff9a262029e3a3e65dc617`.

- [START08.PNG](START08.PNG): DOSBox-X, Windows 3.0 real mode, logical
  640x200 monochrome; 640x400 PNG with doubled rows. My Computer is directly
  on Start. TSHELL build04, SHA-256
  `2c7c0e23f89fe4d91800c55277c98d9a0d69dc81c86058ddee1fe1b71a82441e`.
- [FILES08.PNG](FILES08.PNG): same case/build/mode, native File Manager opened
  through My Computer. A compatibility example, not a redistributed Windows app.
- [CLOCK08.PNG](CLOCK08.PNG): same TSHELL build, DOSBox-X logical 160x200x16;
  640x400 emulator-view capture. The retained 07 date/time editor in build 08.
  It depicts the editor and Cancel-focused state, not proof of clock mutation.
- [NIGHT08.PNG](NIGHT08.PNG): 86Box Tandy 1000 HX, emulated 8088 4.77 MHz,
  640 KB, genuine DOS 6.22, BIOS mode 3 / 80 columns, no ANSI.SYS. Actual normal
  Windows exit, verified restoration, night artwork and returned DOS prompt;
  includes the emulator frame. Final success-only FINISH SHELLSEL, SHA-256
  `6aa652c9fc77e2e05944b46c055157e97b88a10b963135a4aecf5a01fa71c2fd`.

Original paths inside SOURCE.ZIP:

- `START08.PNG`: `evidence/verification/EVIDENCE08/screenshots/acceptance04b-640-02-start-menu.png`
- `FILES08.PNG`: `evidence/verification/EVIDENCE08/screenshots/acceptance04b-640-03-file-manager.png`
- `CLOCK08.PNG`: `evidence/verification/EVIDENCE08/screenshots/acceptance04b-160-08-date-time.png`
- `NIGHT08.PNG`: `evidence/shutdown/finish/EVIDENCE/lifecycle/03-post-windows-night.png`

Current capture SHA-256 identities:

```text
7e507366fff60ae3d47efc7b707346108137d814d60c030c36f18e91c384c6f7  START08.PNG
74d4b88a30d29ee5e357bbbeac5a4200b414f6085bc4940b93a223ae828ad4c7  FILES08.PNG
3b04c54493d1ac357d140712e99f04da5ebabb74661da73ac4ea2f1b6b84d891  CLOCK08.PNG
2aa736ceb11e861b163768e1e382a66a5a9243fad22bc96b7d53529d84fd188e  NIGHT08.PNG
```

## Tandy Start 09 placement correction

[START09.PNG](START09.PNG) is the actual final 09 build01 native Start-menu
capture: DOSBox-X, Windows 3.0 real mode, logical 640x200 monochrome, with
rows doubled to 640x400 by the emulator capture. It replaces START08.PNG
in the root showcase; START08.PNG remains historical evidence. The popup
bottom meets the bar top at logical row 178. It is not a drawn mockup.

TSHELL.EXE: 35,907 bytes, SHA-256
`ad3c8394b3391939f19e2a1cf282d89701fe46397a4ce5c4c7a312f37c6babe6`.
PNG SHA-256: `ff9d2ae6308aa54f23e9553cedf26a2387d5c5c4beb64e786628f25f8208c9e7`.
Original capture: `verification/shell640/02-start.PNG` in the TSTART09
verification package. See [current tests](../../examples/TSHELL/TESTS.MD)
for scope; the picture alone does not establish hardware or lifecycle coverage.

[START160.PNG](START160.PNG) is the companion actual 09 primary-shell
capture at logical 160x200x16. Direct SDL surface capture converted losslessly
from BMP to PNG, with emulator display scaling retained. Source capture:
`verification/shell160/02-start.PNG`. SHA-256:
`e910558163be3d5225b0ed50df3850d385d599509750f1af862f7ce991d4ea26`.
The runtime identity is the same 09 executable listed above.
