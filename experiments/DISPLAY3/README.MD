# Windows 3.0 display drivers

Choose the packet for your hardware. Each contains its ready-built driver;
the current guides describe the native install and normal launch command.

- [Amstrad PC1512](../../docs/PC1512.MD): 640x200, 16 colors, using P15SET.EXE.
- [Plantronics ColorPlus](../../docs/PCP.MD): fixed 320x200 or software-panning
  320x400, 16 colors, using CPPSET.EXE.
- [IBM PCjr](../../docs/SOFTPAN/RELEASE.MD): fixed or software-panning profile
  in one native Setup kit. Its 32 KB video page must already be reserved.
- [Olivetti PC1 and Yamaha](../YAMAHA/README.MD): choose PC1/B000h or the
  distinct standalone B800h hardware profile.
- [Video II](../../docs/tga2/INSTALL.TXT): Tandy SL/2, 640x200, 16 colors.

For Tandy EX/HX or text-mode Windows, use [current downloads](../../docs/DOWNLOADS.MD).

<details>
<summary>Archived 2026-10-12 development and rendering record</summary>

# Experimental display driver packets



The 2026-10-12 release covers three different video systems. PCjr also has a separate clean-Setup repository-file packet, and Yamaha Candidate 03 has two separate experimental profiles. They remain separate from Windows XT rc.6, the Tandy EX/HX release. No TXT40 or TGA-II driver is part of the 2026-10-12 release.



| Machine/card | Driver and mode | Installation/recovery guide |
| --- | --- | --- |
| Amstrad PC1512 | PC1512.DRV, 640x200x16 | [PC1512](PC1512.TXT) |
| IBM PCjr (2026-10-12 release packet) | TNDYJR.DRV, 320x200x16; JRGUARD before every start | [PCjr cloned-install guide](PCJR.TXT) |
| IBM PCjr (clean-Setup repository file) | PCJRSET.ZIP: TNDYJR.DRV, guard/launcher, fonts and PCjr-safe grabber | [Package guide](../../downloads/experimental/PCJR/README.MD); [direct ZIP](https://raw.githubusercontent.com/astrobleem/oemdisplay-tandy/main/downloads/experimental/PCJR/PCJRSET.ZIP), not a release asset |
| IBM XT + Plantronics ColorPlus | PCP3216.DRV, 320x200x16 | [ColorPlus](PCP3216.TXT) |
| Olivetti Prodest PC1, B000h | PC1YAMA.DRV, 160x200x16 | [PC1/B000 candidate ZIP](https://raw.githubusercontent.com/astrobleem/oemdisplay-tandy/main/downloads/experimental/yamaha-candidate03/PC1-B000-CANDIDATE03.ZIP). Build/host checks only; no emulator, Setup or physical PC1 test. [Evidence](../../docs/yamaha/QUALIFICATION.MD) |
| Standalone Yamaha V6355D emulator profile, B800h | YAM160.DRV, 160x200x16 | [B800 candidate ZIP](https://raw.githubusercontent.com/astrobleem/oemdisplay-tandy/main/downloads/experimental/yamaha-candidate03/YAMAHA-B800-CANDIDATE03.ZIP). DOSBox-X raw-VRAM/API results; separate 86Box screenshot, not PC1 qualification. [Evidence](../../docs/yamaha/QUALIFICATION.MD) |



Use a bootable backup/disposable clone of your own Windows 3.0 installation.

The PC1512 and Plantronics rendering tests reused cloned AT/EGA installations.

The older PCJR.ZIP release packet covers a cloned install. The separate

PCJRSET.ZIP repository file passed a DOSBox-X clean-Setup run; its 26/26

session and 40 host tests are documented in the canonical README. Physical

PCjr hardware remains unqualified. Yamaha B800 has a separate 86Box Windows 3.0

screenshot on an IBM XT; the 92-case raw-VRAM/API suite is DOSBox-X and does not

emulate Yamaha scanout. PC1/B000 has build/host checks only; PC1 Setup and physical

PC1 hardware remain untested.

The PC1512 cursor-state failure is unresolved. PCjr has narrower Windows

application coverage and requires an already reserved DOS-owned video page.

The PCjr guard does not reserve RAM. The other video cards have dedicated VRAM.



The 2026-10-12 release packets do not supply a startup logo or run Windows

Setup. PC1512/ColorPlus use the existing `WIN /R`; the released PCJR.ZIP uses

JRWIN's guarded call to the existing `WIN.COM /R`. The later PCJRSET.ZIP

repository file is a separate clean-Setup packet with first-party fonts,

artwork and a PCjr-safe grabber; see its [package guide](../../downloads/experimental/PCJR/README.MD).

It is not a new asset in the 2026-10-12 release. The independent Tandy wave is

not called and there is no automatic fallback or logo selection. A compatible

stock Windows loader may show Microsoft's static logo; a modified one may show

other art. The PCjr test clone used original CGA logo code plus our static

WXTSPL01.RLE; logo pixels and stock-logo compatibility were not separately

tested.



Runtime pins and historical evidence are from

[ba980d4ccf9092c38ea22b006373f420d0f059e2](https://github.com/astrobleem/oemdisplay-tandy/commit/ba980d4ccf9092c38ea22b006373f420d0f059e2).

[Native rebuild/launcher evidence](NATIVE.JSN) records exact driver/staged

source matches, 14 control cases, actual guard acceptance/refusal and two

guarded Windows 3.0 start/normal-exit cycles at 320x200x16. Unchanged driver

bytes retain their historical rendering scope; this new run checks display

caps and normal exit, not a fresh full rendering oracle.



Yamaha Candidate 03 remains separate from the five original Tandy profiles in [docs/MODES.MD](../../docs/MODES.MD). The two driver ZIPs and source/evidence archive are experimental repository-file downloads, not assets in the 2026-10-12 release: [PC1/B000](https://raw.githubusercontent.com/astrobleem/oemdisplay-tandy/main/downloads/experimental/yamaha-candidate03/PC1-B000-CANDIDATE03.ZIP), [B800](https://raw.githubusercontent.com/astrobleem/oemdisplay-tandy/main/downloads/experimental/yamaha-candidate03/YAMAHA-B800-CANDIDATE03.ZIP), [source/evidence](https://raw.githubusercontent.com/astrobleem/oemdisplay-tandy/main/downloads/experimental/yamaha-candidate03/YAMAHA-CANDIDATE03-SOURCE-EVIDENCE.ZIP). See the [Yamaha guide](../YAMAHA/README.MD) and [corrected evidence summary](../../docs/yamaha/QUALIFICATION.MD).



## Developer verification



`python3 experiments/DISPLAY3/TESTPKG.PY` runs synthetic host refusal tests.

It runs no emulator and uses no private inputs. The synthetic fixtures are

never public runtime candidates.



`pwsh -File experiments/DISPLAY3/TESTLOCK.PS1` tests wrapper refusals using

synthetic locks and a nonexistent worker executable; it launches no emulator.

Native qualification requires a separately allocated slot and an explicit

`-LockPath` naming that host's existing shared lock. The wrapper never creates

or substitutes a private lock. Supply the remaining required paths shown by

`Get-Help experiments/DISPLAY3/NATIVE.PS1 -Full`; use fresh owned output.



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


</details>
