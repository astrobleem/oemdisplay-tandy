# Windows XT user manual

[Project and downloads](../README.md) · [Install](RELEASES/RC8.MD) ·
[XR1 controls](RELEASES/RC8.MD#what-is-current) · [Tandy Start](#use-tandy-start) ·
[Experimental drivers](#separate-experimental-drivers) ·
[Repair](RELEASES/RC8.MD)

Windows XT adds a compact Start-menu desktop, color graphics, original fonts,
games and utilities to **Windows 3.0 real mode on a Tandy 1000 EX/HX with
640 KB RAM**. Use the [current downloads](DOWNLOADS.MD) for your display profile or the
complete desktop bundle. You supply DOS and Windows.

![Windows XT startup wave captured in DOSBox-X at native 320x200 pixels](PROMO/XTWAVE.GIF)

*Actual emulator capture of the accepted Color startup wave.
[Capture details](PROMO/XTWAVE.JSON). Physical hardware performance is unqualified.*

## Download and install

For the Tandy EX/HX panning display, [download XRSYNC.EXE](https://github.com/astrobleem/oemdisplay-tandy/releases/download/xrsync-dos-2026-10-24/XRSYNC.EXE).
Exit Windows and run `XRSYNC C:\WINDOWS` from DOS, then follow the
[Setup choices](RELEASES/XRSYNC.MD). Use `C:\XR155\RUNSYNC.BAT` on every launch.

For the full Tandy Start desktop bundle, use [desktop setup](DESKTOP.MD).
For fixed-resolution graphics or other hardware, use [current downloads](DOWNLOADS.MD).
Each is a product/profile choice; no older-release installation chain is needed.

## Use Tandy Start

Tandy Start provides a compact Start button and clock bar. Program Manager
continues to edit your program groups; close and reopen Programs after saving
a group to refresh its contents. Existing groups are read-only to the shell.

| Control | What it does |
| --- | --- |
| **Programs** | Reads existing Program Manager groups, preserving arguments and working directories. The disk also supplies a Windows XT group with saver previews, About and Pinball. |
| **My Computer** | Opens or restores File Manager. |
| **Run → Browse** | Chooses an executable and launches it from its folder. Type DOS short paths in Run. |
| **System** | Opens About This Tandy and screen-saver settings. |
| **Clock** | Double-click for Clock/Calendar; right-click to adjust date and time. |
| **Exit Windows** | Confirms exit and lets apps ask about unsaved work. Hold Shift while selecting Exit to skip its chime. Enter or Escape initially cancels; E selects Exit. |

Maximized apps can cover the bar; it is not an application taskbar.
The current desktop packet includes the matching Tandy Start and TSINPUT
files. Use the [desktop guide](DESKTOP.MD) for installation and recovery.

### Browse existing long filenames

Run → Browse can show existing VFAT long names, including spaces. It always
navigates and launches using the **DOS short alias** shown below the list.
Labels are read-only; the shell does not create or rename long names or add
long-path support to other programs.

The verified reader requires **genuine DOS 6.22, Windows 3.0 real mode, and a
fixed, uncompressed local FAT12/FAT16 volume with 512-byte sectors**. This is
narrower than the installer's DOS 3.3+ requirement. Removable/floppy, network,
FAT32, SUBST/JOIN/ASSIGN and detected DriveSpace volumes use short names.
An emulator host-folder mount is outside the qualified raw-volume domain.

Listings above 128 filtered rows, unsupported or ambiguous entries, read
errors and exhausted limits fall back to aliases. Labels over 63 characters
are shortened with an ellipsis. [Requirements and fallback details](../distributions/WINXT/NAMES11.TXT).

### Keyboard, mouse and joystick

The ordinary Start button works with the stock keyboard driver. Optional
**Hold-to-Start** requires the supported real-mode Tandy ROM profile, a
compatible loaded keyboard driver and TSINPUT. A plain press/release of Hold
opens Start over another app; Escape returns focus. Modifier combinations,
modal dialogs and saver wake-up have separate handling.

The desktop bundle installs `TNDYK3.DRV` and the matching `TSINPUT.DLL`.
The standalone [TNDYK3 candidate guide](../src/tandyk3/README.md) retains its
own guarded installer and rollback. Its separate K3TOOLS packet contains
probes, rather than the driver. Raw hardware press/release observations do
not qualify Windows key translation or physical Hold behavior.
[Hold support and scope](../distributions/WINXT/HOLD14.TXT).

[EXJOY](../examples/EXJOY/README.MD) is an optional raw joystick diagnostic
with session-only calibration; physical input remains unverified. The public
[DOS wheel diagnostic](../tools/WHEEL/README.TXT) probes wheel/API and serial
data; it does not install Windows scrolling. The desktop bundle supplies the
first-party `WHEEL.DRV`, the `WXTWHL.EXE` client and their startup configuration.
Use the [desktop guide](DESKTOP.MD) for that combined wheel setup.

### Screen savers and sound

**System → Screen saver** selects None, Matrix, Maze or Starfield. Delay is
10–3600 seconds; Preview tries unsaved choices and Apply saves them. Starfield
has speed and 16/32/64-star options; sixteen stars is the lightest setting.
Maze can be very slow. These savers are visual effects, not password locks.

Tandy Start offers optional Tandy or XP-note startup and exit phrases. The
chime apps use the PSG directly; the optional Computer preset does not enable
PSG sound. Run only one PSG producer at a time. Hold Shift while choosing
Exit to skip its sound.

The separate **[OEMSound-Tandy](https://github.com/astrobleem/oemsound-tandy)**
project supplies Mini MIDI, Mini Piano, Beats Lab, Automatic Mouth, PSGPLAY
and other experiments. Start with its [current sound installation guides](https://github.com/astrobleem/oemsound-tandy#try-it)
and choose the app you want. App-local MIDIMAP is not a system MIDI device or General
MIDI synthesizer.

## Games and utilities

The desktop bundle includes Pinball, About, Matrix, Starfield and Maze.
Other apps have their own packet and guide.

| App | What to try |
| --- | --- |
| [Pinball](../examples/PINBALL/README.MD) | Space launches; Z/Left and / or Right control the flippers; P pauses. |
| [Cookie Clicker](../examples/COOKIE/README.MD) | Click or press Space, buy upgrades, save and load. Fits 160×200. |
| [Fly Swat](../examples/SWAT/README.MD) | Mouse-controlled fly hunting, pause/restart, windowed and fullscreen paths. |
| [Maze game/saver](../examples/MAZE/GAME/README.MD) | Included in the desktop bundle. |
| [Tandinator](../examples/TANDINAT/README.MD) | Character guessing; [0.3.8](../experiments/TANDI11/README.MD) is a separate experimental packet. |
| [Green hill wallpaper](../examples/HILLS/README.TXT) | Native landscapes for the 160/320-pixel sixteen-color modes. |
| [XTEyes](../examples/XTEYES/README.TXT) / [Slosh](../examples/SLOSH/README.MD) | Pointer-following eyes and a tiny moving water surface. |
| [GIFLOAD](../examples/GIFLOAD/README.TXT) | Converts supported static GIFs to new palette-mapped BMPs for Paintbrush. |
| [App-local dialogs](../examples/COMMDLG/README.TXT) / [FileDrop](../examples/FILEDROP/README.TXT) | Demo-specific file dialogs and path-name transfer. |

Stock Windows apps shown in captures, including Paintbrush, Notepad and File
Manager, come from your own installation. The [TANDYLAB catalog](../examples/TANDYLAB/CATALOG.TXT)
and [optional experimental release](https://github.com/astrobleem/oemdisplay-tandy/releases/tag/experiments-2026-10-07)
list additional packets. Alternate shells and app overlays are not automatically
combined; read each packet's dependencies and rollback instructions.

## Separate experimental drivers

Choose the packet for your machine and follow its installer and launcher.
The current downloads below are separate from the EX/HX desktop.

### TEXT80 and compact C25

Download **[TEXT80.ZIP](../downloads/experimental/TEXT80/TEXT80.ZIP?raw=1)**,
read its [packet guide](../downloads/experimental/TEXT80/), and extract the
complete runtime folder to a writable DOS 8.3 path. It contains first-party
fonts and helpers; your own working Windows 3.0 installation remains required.

| Profile | Driver | Screen and purpose |
| --- | --- | --- |
| **C25** | `T80CMP.DRV` | 80×25 text, 640×200 logical desktop, compact character-cell controls. |
| 25 | `TEXT80.DRV` | 80×25 text, 640×200 logical desktop, standard controls. |
| PAN | `T80PAN.DRV` + `XTPAN.EXE` | An 80×25 view over a 640×400 logical desktop; uses more Windows memory. |
| VGA | `T80VGA.DRV` | Full 80×50 text, 640×400 logical desktop; requires VGA. |

CGA-compatible color adapters are the target for C25, 25 and PAN. Physical
adapters have not been qualified; a real IBM CGA can show snow. Large fonts,
icons and graphics appear as block approximations. C25 gives exact compact
controls when windows align to the eight-pixel grid; some dialogs and off-grid
controls remain approximate. Scrolling can take seconds on an emulated XT.

Extract to `C:\TEXT80`, exit Windows and run from plain DOS:

```bat
C:
CD \TEXT80
T80ON C:\WINDOWS C25
```

After the setup success message, use your existing required memory guard,
then start Windows from its own directory:

```bat
C:
CD \WINDOWS
WIN /R
```

Use your actual Windows installation directory. To
change profile, exit Windows and run `T80OFF C:\WINDOWS` from the packet folder
before running `T80ON` again with `25`, `PAN`, `VGA` or `C25`. In PAN, with
NumLock off, **Alt+PgDn / Alt+PgUp** pan and **Alt+F9** returns to the top;
the helper also follows windows and pointer-edge dwell.

To undo from DOS, run `T80OFF C:\WINDOWS` from the runtime folder. It removes
its recorded INI changes while preserving unrelated later settings. Keep its
state and backup files until rollback succeeds. If it reports a damaged or
missing record, stop and read the [recovery instructions](TEXT80.MD#7-installing-and-removing-dos)
before using whole-file `T80SET RESTORE`, which discards later INI edits.
After rollback, use the previous display's required launcher; a Tandy graphics
installation still requires its video-memory guard.

The C25 driver matches the exact binary in the recorded **54/54** Windows
session on an emulated IBM XT/CGA. Current rebuilt TEXT80 25, PAN and VGA
bytes have fresh audits and presenter tests, but their earlier Windows GUI
sessions used older hashes; those rebuilt bytes have not booted in Windows here. See the packet's
qualification record for each profile's exact identity and test scope.
[Detailed behavior, evidence and limitations](TEXT80.MD).

### IBM PCjr clean Setup

Download **[PCJRSET.ZIP](../downloads/experimental/PCJR/PCJRSET.ZIP?raw=1)**
and follow the included `INSTALL.TXT`. Copy its complete install folder to
**`C:\PCJREXP`**. The fixed path matters to Setup and its launcher.

This experimental driver provides **320×200 in 16 colors**. You need your own
Windows 3.0 media, DOS, a hard disk and suitable PCjr memory expansion. Before
Setup, run:

```bat
C:\PCJREXP\JRGUARD
```

Continue only after **OK**. The guard checks that the 32 KB video page at
segments 1800h–1FFFh is already excluded from DOS allocation; **it does not
reserve RAM**. Run your own Windows Setup, select **Other display**, point it
to `C:\PCJREXP`, and choose **EXPERIMENTAL IBM PCjr 320x200 16 colors**. Choose
the PC/XT 84-key keyboard and the mouse option matching your hardware. Follow
the packet's remaining Setup choices and **return to DOS**, rather than
restarting Windows from Setup.

Start Windows every time with:

```bat
C:\PCJREXP\JRWIN
```

The clean-install Windows Setup flow passed **26/26 emulator checks**, and
this packet's driver matches the qualified pin. Real PCjr memory expansions,
keyboard, serial input and timing remain unqualified. PCjr-only DOS video
modes cannot switch away with Alt+Tab; finish that DOS program to return.
[Full installation, existing-install and recovery guide](../src/pcjr/INSTALL/INSTALL.TXT) ·
[Native session record](pcjr/INSTALL/SESSION.JSN).

### Panning

For EX/HX graphics panning, use the [XRSYNC display](RELEASES/XRSYNC.MD).
Ctrl+Alt+arrows move its 320x200 view over the 640x256 desktop;
Ctrl+Alt+Home returns home. XYCTL selects software or hardware presentation.

TEXT80 PAN provides an 80x25 view over 80x50 logical rows. Its larger shadow
uses more Windows memory. [Text panning controls and memory](TEXT80.MD#3-memory).

### Other video hardware

| Machine/card | Driver and installation guide |
| --- | --- |
| Tandy Video II, emulated SL/2 family | [TNDYV2.ZIP](https://raw.githubusercontent.com/astrobleem/oemdisplay-tandy/main/downloads/experimental/TGA2/TNDYV2.ZIP) and [Setup/recovery](tga2/INSTALL.TXT). Use INSTALL for Setup and T2WIN for every start; both reserve video memory automatically. **EX/HX must not use it.** |
| Amstrad PC1512 | [PC1512 experimental packet](https://github.com/astrobleem/oemdisplay-tandy/releases/download/experimental-displays-2026-10-12/PC1512.ZIP) and [guide](../experiments/DISPLAY3/PC1512.TXT). |
| IBM XT + Plantronics ColorPlus | [PCP3216 experimental packet](https://github.com/astrobleem/oemdisplay-tandy/releases/download/experimental-displays-2026-10-12/PCP3216.ZIP) and [guide](../experiments/DISPLAY3/PCP3216.TXT). Requires the card and its dedicated VRAM. |

These have separate Windows 3.0 real-mode evidence and hardware limits. Other
Video II models are unqualified. [Olivetti PC1/Yamaha candidates](../experiments/YAMAHA/README.MD)
have separate experimental packets; standalone Yamaha emulator evidence does
not qualify physical PC1 hardware.

## Recovery

For XRSYNC, use its [DOS Setup and RUNSYNC procedure](RELEASES/XRSYNC.MD).
For the desktop bundle, use `C:\FIXXT` from plain DOS as described in
[desktop setup](DESKTOP.MD). For TEXT80, run `T80OFF` from its extracted folder.
PCjr and the other hardware drivers use the Setup/removal instructions in
their own guides. Recovery depends on the installed product/profile.

## Test scope and useful reports

The driver guides identify their tested hardware or emulator scope.
Windows 3.0 real mode is required; Windows 3.1 is unsupported.

A useful issue report includes the machine and RAM, DOS/Windows versions,
package name, mode, exact steps, expected and actual behavior,
and whether it ran on hardware or an emulator.

[Development status](STATUS.MD) · [Build guide](../BUILDING.MD) ·
[Graphics mode contracts](MODES.MD)

Preserve component licenses and notices. Repository access does not grant
rights to Windows media, ROMs, proprietary fonts, compilers or emulators;
keep those out of redistributed packets.
