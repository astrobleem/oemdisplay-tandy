# Experimental display driver packets

These packages target three different video systems. They are separate from
Windows XT rc.6, which remains the Tandy EX/HX release. No TXT40 or TGA-II
driver is part of this packet.

| Machine/card | Driver and mode | Installation/recovery guide |
| --- | --- | --- |
| Amstrad PC1512 | PC1512.DRV, 640x200x16 | [PC1512](PC1512.TXT) |
| IBM PCjr | TNDYJR.DRV, 320x200x16; JRGUARD before every start | [PCjr](PCJR.TXT) |
| IBM XT + Plantronics ColorPlus | PCP3216.DRV, 320x200x16 | [ColorPlus](PCP3216.TXT) |

Use a bootable backup/disposable clone of your own Windows 3.0 installation.
Historical rendering tests reused cloned AT/EGA installations. The new PCjr
launcher qualification uses an owned Windows 3.0 clone with EGA fonts and
CGA.GR2. Fresh Setup/font/grabber integration, DOS boxes and physical hardware
remain unqualified.
The PC1512 cursor-state failure is unresolved. PCjr has narrower Windows
application coverage and requires an already reserved DOS-owned video page.
The PCjr guard does not reserve RAM. The other two cards have dedicated VRAM.

Runtime pins and historical evidence are from
[ba980d4ccf9092c38ea22b006373f420d0f059e2](https://github.com/astrobleem/oemdisplay-tandy/commit/ba980d4ccf9092c38ea22b006373f420d0f059e2).
[Native rebuild/launcher evidence](NATIVE.JSN) records exact driver/staged
source matches, 14 control cases, actual guard acceptance/refusal and two
guarded Windows 3.0 start/normal-exit cycles at 320x200x16. Unchanged driver
bytes retain their historical rendering scope; this new run checks display
caps and normal exit, not a fresh full rendering oracle.

## Developer verification

`python3 experiments/DISPLAY3/TESTPKG.PY` runs synthetic host refusal tests.
It runs no emulator and uses no private inputs. The synthetic fixtures are
never public runtime candidates.

`PACKAGE.PY build` consumes exact pinned qualified drivers plus a matching
native launcher record, release-owner authorization/notices and two
complete source commit pins. It produces three runtime ZIPs, one matching
adaptation-source companion, qualification JSON and checksums. Outputs must
be fresh. Only allowlisted files are published; compiler/DDK/Windows/DOS/ROM
inputs and destructive negative-test COM helpers are excluded.

`PACKAGE.PY verify --out <packet> --publication` additionally refuses
missing owner authorization/notices or incomplete native launcher/Windows
qualification. Do not bypass that gate or silently change runtime pins.
The adaptation-source companion needs a separately authorized generic
renderer/DDK source view to rebuild. New packaging/launcher code has its own
MIT license; that license does not relicense the reused Microsoft renderer
or resources. Historical DDK license-envelope terms are not present in the
materialized inputs, and the packet does not assert a blanket license grant.
