# Windows XT v0.1.0-rc.8 - current XR1 own-media installer

This package installs the completed XR1 desktop from your Windows 3.0 media.
It supplies the shell, helpers, adapted display/keyboard drivers, wheel driver,
original fonts and artwork. No previous private R1 build folder is required.
The earlier downloads remain available with their original contents.

## Downloads

- [XR1 installer package](https://github.com/astrobleem/oemdisplay-tandy/releases/download/v0.1.0-rc.8/WINXT-XR1.ZIP).
- [Converted Minesweeper app and About shim](https://github.com/astrobleem/oemdisplay-tandy/releases/download/v0.1.0-rc.8/WINMINE30.ZIP), with installation instructions and notices.
- [Start here](https://github.com/astrobleem/oemdisplay-tandy/releases/download/v0.1.0-rc.8/START-HERE.TXT),
  [qualification](https://github.com/astrobleem/oemdisplay-tandy/releases/download/v0.1.0-rc.8/QUALIFY.JSON),
  [release identities](https://github.com/astrobleem/oemdisplay-tandy/releases/download/v0.1.0-rc.8/RELEASE.JSON)
  and [checksums](https://github.com/astrobleem/oemdisplay-tandy/releases/download/v0.1.0-rc.8/SHA256SUMS).

## Prepare and install

Use an original Tandy 1000 EX/HX with 640 KB, DOS 3.3+ and Windows 3.0 real mode.
On a modern computer, extract WINXT-XR1.ZIP and run its Python 3.8+ preparer:

```text
python PREPARE.PY --windows-media C:\WIN30SRC --mode fresh --out C:\XR1NEW
```

Supply a merged folder from the supported English Windows 3.0 media set.
The tool accepts expanded files and original mode-A SZDD files, validates
exact input hashes and refuses a different media set before creating output.
For an existing installation, use `--mode update` and a different new output
folder. Update preparation requires the matching CGA.GR2, WIN.CNF and original
SETUP.INF files; fresh preparation also imports the Windows Setup files.

Back up Windows. Transfer the prepared DOS-CROOT contents to DOS C:\ using
your normal storage procedure, preserving DOS boot files and configuration.
From plain DOS run `C:\SETUPXT`. Fresh Setup uses C:\WINDOWS: choose the
first Tandy 1000 EX/HX Computer entry, HPXY 640x256, PC/XT keyboard, COM1 wheel
mouse and No Changes for DOS configuration. The existing-install route
updates the components and preserves unrelated INI settings/customization.
Start afterward with `C:\STARTXT`; repair with `C:\FIXXT` or request complete
file comparison with `C:\FIXXT /VERIFY`. Keep the installer journal and your
backup if installation is interrupted. START-HERE explains recovery.

Windows and DOS are supplied by you. The tool generates CNF.PIN, XTTEST.COM
and modified Setup metadata locally from those files. Keep the prepared
DOS-CROOT and assembled Windows installation private; those outputs contain
Windows bytes. The public package contains neither a Windows distribution
nor a bootable DOS disk, compiler or emulator.

## What is current

XR1 provides a **640x256 logical desktop viewed through 320x200 in sixteen
colors**, Tandy Start, keyboard panning, hardware presentation controls and
COM1/IRQ4 serial mouse input with optional wheel data. XYCTL starts in Software
mode; its menu or Ctrl+Alt+H enables Hardware presentation. Ctrl+Alt+arrows
pan and Ctrl+Alt+Home returns home. Other custom display profiles remain
separate packages. The existing qualified executable binaries are preserved;
this release completes their own-media packaging and XR1-only setup guides.

Minesweeper is a separate download, not installed by SETUPXT. Its packet
includes the existing converted WINMINE.EXE and WMABT.DLL About shim, a short
installation guide, hashes and the exact prior test scope. The app is adapted
from Microsoft Windows Minesweeper; the shim's source/build project was not
recovered, so the packet makes no complete source-reproduction claim.

## Verification and notices

The final preparer is checked against the matching owned media and tested
with 24 host boundary cases. The deterministic publisher has nine synthetic
tests and verifies a closed six-asset release, every source hash, native
fresh/update qualification, ZIP contents and checksums. Fresh installation
and update are tested separately on the original 8088, 640 KB HX emulator
configuration. QUALIFY.JSON records their exact run IDs and cleanup results.
The prior Oct19 runtime integration separately covers four wheel checks,
eight exact viewport frames and two clean DOS returns.

[Fresh/update receipts](../QUAL/XR1/INSTALL.JSN) bind the tested preparation
and installed components. Unmodified post-install Windows captures are kept
for [fresh installation](../QUAL/XR1/FRESH.PNG) and [update](../QUAL/XR1/UPDATE.PNG).

This final package and wheel driver have emulator qualification. Earlier
physical EX panning acceptance is separately scoped; no new hardware run,
other-profile qualification or Windows 3.1 support is claimed. Large redraws
and some applications remain slow on the original 8088.

NOTICE.TXT identifies the Windows 3.1 DDK-derived HPXY and TNDYK3 adaptations
and retains their Microsoft notices. The runtime target remains Windows 3.0.
The original wheel/font/artwork components retain their own MIT notices;
other components keep their applicable notices. No blanket MIT license or
new Microsoft license grant is asserted for the combined package.

For historical downloads, see [rc.7](RC7.MD) and
[rc.6](https://github.com/astrobleem/oemdisplay-tandy/releases/tag/v0.1.0-rc.6).
