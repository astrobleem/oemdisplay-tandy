# TEXT80 and compact C25 — experimental download

**[Download TEXT80.ZIP](https://raw.githubusercontent.com/astrobleem/oemdisplay-tandy/main/downloads/experimental/TEXT80/TEXT80.ZIP)** · [SHA-256](SHA256.SUM) · [Detailed behavior](../../../docs/TEXT80.MD)

Windows 3.0 real mode, 8086/8088, 640 KB. This separate 2026-10-18 packet
contains four text display profiles, the DOS installer/rollback program,
panning helper and original XT Pixels fonts. It does not replace Windows XT
rc.6 or its historical TXTMODE experiment. No physical hardware is qualified.

| Profile | Driver | View and desktop | Exact evidence for this download |
| --- | --- | --- | --- |
| **C25** | T80CMP.DRV | 80×25, compact controls, 640×200 | Matches the recorded 54/54 Windows GUI session binary. |
| 25 | TEXT80.DRV | 80×25, 640×200 | Fresh 8086/link/REP-prefix audits and presenter tests; earlier GUI session used a different hash. |
| PAN | T80PAN.DRV | 80×25 viewport over 640×400 | Fresh audits and panned presenter tests; earlier GUI session used a different hash. |
| VGA | T80VGA.DRV | 80×50, 640×400, VGA only | Fresh audits and full-height presenter tests; earlier GUI session used a different hash. |

The current 25/PAN/VGA driver bytes have not been booted in Windows here.
C25 is byte-identical to the earlier tested driver. T80SET.EXE matches its
later recorded DOS-tested build and passes fresh compact/rollback fixtures.
Scrolling is slow; graphics and larger fonts appear as block approximations.
C25's compact controls are exact only when aligned to the text-cell grid.

## Install and undo

Back up a working Windows 3.0 installation. Extract the `TEXT80` folder to
`C:\TEXT80`. From plain DOS, after exiting Windows:

```bat
C:
CD \TEXT80
T80ON C:\WINDOWS C25
```

Use your actual Windows directory. Read the result and start with `WIN /R`
from that Windows directory only after setup succeeds. Retain any existing
machine-specific memory guard required by your installation. Normal `25`,
`PAN` and VGA-only `VGA` are alternative profile arguments. PAN uses about
100 KB more Windows memory; Alt+PgDn / Alt+PgUp and pointer-edge dwell pan.
To change profiles, exit Windows and run T80OFF first.

Undo from the extracted folder at the DOS prompt:

```bat
T80OFF C:\WINDOWS
```

No manual INI edits are needed. Other settings, existing load entries and
fonts are preserved. Keep SYSTEM.T80, WIN.T80 and T80SET.STA until rollback
succeeds. Damaged state causes refusal without changes; explicit
`T80SET RESTORE` restores whole backups and discards subsequent INI changes.
Read `TEXT80/INSTALL.TXT` inside the ZIP before using recovery.

## Verification and source

The ZIP is **389,699 bytes**, SHA-256
`ed96bba2d247f8d203be61675968a4ba7cfb1a681dd5f0be794ce66af1577758`.
Each member is bound by `TEXT80/SHA256.SUM`; `BUILD.JSN` records exact source,
compiler, emulator, payload and test identities. Two independent package
runs produced identical ZIP bytes. All runtime filenames use DOS 8.3 names.

[Build and packaging recipe](../../../tools/EXPPUB/README.MD) ·
[Qualification record](../../../tools/EXPPUB/QUALIFY.JSN) ·
[Runtime source snapshot](https://github.com/astrobleem/oemdisplay-tandy/tree/997e7b910eb4623226b676c1c229aa0dd4e81661/src/text80).
The download contains no Windows/DOS media, Microsoft fonts, retail grabber,
ROM, compiler, emulator or credentials. Display derivatives retain DDK
notices; the included original XT Pixels fonts have their own MIT license.
