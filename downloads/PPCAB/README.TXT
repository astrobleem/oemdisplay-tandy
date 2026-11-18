PRIVATE PPC512 CGA100 A/B - NOT A RELEASE OR A DIAGNOSIS

Purpose
Compare the original CGA100 blanking policy with video left enabled during
VRAM conversion/cursor work. This is for the existing CGA 160x100 profile,
not the panning driver, CGA320/640, compact profiles or the whole suite.
Reported external-display flicker via MCE2HDMI is the observation to test;
internal-LCD behavior has not been established.

A: CGABASE.DRV is byte-identical to CGA100.DRV in the original CGA.ZIP.
The native source rebuild reproduced those released bytes exactly.
B: CGALIVE.DRV was built from the same staged source with one instruction
operand changed in cga_vram_begin: MOV AL,01h becomes MOV AL,09h before
OUT DX,AL at port 3D8h. Entry now leaves video enabled; exit still writes
09h. Initialization still blanks while programming the mode, unchanged.
Nesting, depth, registers, saved FLAGS/IF/DF, conversion, cursor code, CRTC
timings, palette and instruction sizes/cycles are unchanged. Final driver
files differ in exactly this one byte. SOURCE contains both helper forms.

All supplied fonts/grabber/logo files are the original CGA packet bytes.
None of the separate System-font improvement candidate is included.
There is no installer, updater, version check or automatic recovery system.
Keep this package private until separate distribution is authorized.

Before installation - plain DOS only
Use an existing working CGA100 installation from the original CGA packet.
Do not use this kit to install Windows or to replace a custom font setup.
Keep the same applications, fonts and Windows settings for A and B.
Exit Windows completely; do not copy files or run Setup in a DOS window.
Keep a bootable DOS disk and sufficient space for a full Windows backup.
Examples use C:\WINDOWS; substitute the actual installed Windows directory.

Extract this ZIP at C:\ so the source is C:\PPCAB\DRIVERS.
Before proceeding, make a NEW backup directory. If C:\PPCSAVE already
exists, use a different unused directory throughout; never overwrite your
only earlier backup. From plain DOS:
  MD C:\PPCSAVE
  XCOPY C:\WINDOWS C:\PPCSAVE /S /E
Check that the backup contains SYSTEM.INI, WIN.INI, WIN.COM and SYSTEM with
your existing driver and fonts. If backup fails or space is insufficient,
stop. Keep the original CGA source packet as well.

CGABASE.DRV and CGALIVE.DRV are separate names: existing CGA100.DRV is not
replaced. If either private name already exists in your Windows directory
or SYSTEM folder, stop and resolve that older trial before continuing.

Select A using ordinary Windows Setup
  C:
  CD \WINDOWS
  SETUP
Choose Display, then Other display, and enter C:\PPCAB\DRIVERS.
Select "CGA100 A - original blanking (private)". Complete Changes.
If asked for the display disk, give that SAME folder again.
If Setup asks about CONFIG.SYS, select 3.) Setup can make NO changes for
you, then press ENTER. Do not select either configuration-writing choice.
Setup may next request Microsoft Windows 3.0 Disk #1 for WIN.CNF. Give
your ORIGINAL Windows OS disk/source folder at that prompt, not the PPCAB
driver folder. Complete Setup before starting Windows. Do not change
AUTOEXEC.BAT, memory or other hardware for this comparison.
Cold-start Windows using your existing normal CGA startup path; respect
any existing guard/error. The result must be the same 160x100 profile.
If it is not, exit and restore before proceeding.

Compare A and B
For A, observe at least 30 seconds of idle desktop, 30 seconds moving only
the mouse (including edges), then the same repeated repaint activity:
open/close a menu and dialog, move a window and scroll the same document.
Record brightness pulsing/flicker, snow/sparkles, cursor trails, corruption,
responsiveness, hangs and return to DOS. Keep the display connection and
all other settings fixed. Note whether the effect occurs while idle,
mouse-only, repaint-only or throughout.
Exit Windows completely. Repeat the DOS Setup steps, selecting
"CGA100 B - nonblanking (private)". Cold-start and repeat the same actions.
Then select A again and repeat briefly to check the observation repeats.
If practical, repeat A/B on the internal LCD as well as the external
MCE2HDMI path; identify which output each observation came from. A short
video with the variant/output/activity identified is useful. Do not change
fonts, applications, timings, adapter settings or other drivers between A/B.

Stop and restore
If B produces snow, corruption, a hang or any other regression, stop using
B and restore A. Exit Windows and select A in DOS Setup as above. After a
hang, boot plain DOS from the known-good boot disk before doing this.
To restore the exact pre-test configuration instead of selecting A, from
plain DOS copy the saved files back (use your actual backup path):
  COPY C:\PPCSAVE\SYSTEM.INI C:\WINDOWS\SYSTEM.INI
  COPY C:\PPCSAVE\WIN.INI C:\WINDOWS\WIN.INI
  COPY C:\PPCSAVE\WIN.COM C:\WINDOWS\WIN.COM
If DOS asks to overwrite these three current files, confirm the copies
from your saved backup. Your original CGA100.DRV was not overwritten.
Keep the full Windows backup
until a successful cold start and clean DOS return; use it for full recovery
if needed. Leave private driver files unused until testing is finished.

Actual limited emulator checks
DOSBox-X 2025.02.01, CGA, normal 640 KB, Windows 3.0 real mode,
8086-prefetch core, no EMS/XMS/UMB. Both distinct driver names cold-started
at logical 160x100 with the original fonts, menus and a dialog. Five cursor
positions included clipped corners; hiding restored exact visible VRAM,
and repaint beneath an XOR cursor restored clean pixels after hiding.
Both returned to DOS with mode, columns, page and cursor shape restored.
A/B matched exactly in 11 visible VRAM scenes, five independent Windows
GetPixel captures and all 224 System character advances. Source/listing and
whole-driver comparison verify the single mode-control operand difference;
there was no emulator I/O trace or physical timing measurement.
Ordinary DOS Windows Setup committed A, then B, then A again from this
package's two OEM choices. Each actual SYSTEM.INI selection, installed
driver and original fonts was checked, followed by a successful cold start
and clean DOS return. Setup's CONFIG.SYS question was answered NO changes;
the original OS media supplied WIN.CNF. No root configuration files were
created. The README's DOS COPY restoration of SYSTEM.INI, WIN.INI and
WIN.COM restored their saved pre-test bytes exactly; the untouched original
CGA100.DRV then cold-started successfully with the same rendering/cursor
checks and clean DOS return. Those restored files remained byte-identical
to the pre-test backup after the final cold start.
These checks cannot establish PPC512 bus contention, physical snow,
MCE2HDMI synchronization or flicker behavior. No PPC512, internal LCD or
external adapter hardware test has been performed. This is a hypothesis
comparison, not a diagnosed or resolved flicker problem.
