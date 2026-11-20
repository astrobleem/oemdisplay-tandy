PPC512 OPTIONAL LARGER 160x100 SYSTEM UI - EXPERIMENTAL TESTER

Purpose
Compare the revised five-row System face against an original six-row face,
keeping the hardware-tested B nonblanking driver byte-for-byte unchanged.
Alex reported B eliminated flicker on his setup; this test addresses size
and readability. This does not change the released defaults or add panning.
C:\PPCUI\B selects CGALIVE.DRV plus revised five-row CG1SYS.FON.
C:\PPCUI\BIG selects PPC6.DRV plus six-row PPCSYS6.FON.
PPC6.DRV is an exact copy of B, not a new rendering/timing variant.
Both retain the original four-by-six Fixed and Terminal fonts.

Install and restore through ordinary Setup, from PLAIN DOS
Use an existing working CGA100/B Windows 3.0 installation. Keep bootable
DOS, the existing PPCAB kit and your licensed original Windows media.
Exit Windows completely; do not run Setup or copy modules in a DOS window.
Make a NEW full backup of the Windows tree to an unused directory first.
For example (substitute actual paths; never overwrite an earlier backup):
  MD C:\UISAVE
  XCOPY C:\WINDOWS C:\UISAVE /S /E
Check SYSTEM.INI, WIN.INI, WIN.COM and SYSTEM with your drivers/fonts were
saved. Stop if backup fails or space is insufficient.
Extract this ZIP at C:\ to obtain C:\PPCUI\B and C:\PPCUI\BIG.
Stop if an older PPC6.DRV or PPCSYS6.FON trial already exists in WINDOWS
or SYSTEM; resolve that older trial first.
  C:
  CD \WINDOWS
  SETUP
Choose Display, Other display, then C:\PPCUI\BIG. Select the larger
six-row entry and Complete Changes. If asked for the optional display disk,
give C:\PPCUI\BIG again. When the filename shown at the bottom is CGA.GR2 or WIN.CNF, supply your
ORIGINAL WINDOWS media containing that file, not this tester folder. The
CGA.GR2 prompt may have an empty disk label. For XTSTATIC.LGO, WXTSPL01.RLE
or a project font, switch back to the matching BIG or B folder. Setup can
switch between those sources; follow the filename shown at the bottom.
The Microsoft grabber is deliberately not distributed in this archive.
Decline unrelated CONFIG.SYS/AUTOEXEC.BAT changes. Start WIN /R normally.
To restore B: exit Windows fully, run DOS SETUP again, choose Other display
from C:\PPCUI\B, select the five-row entry, and Complete Changes. Supply
that same B folder for its display-disk prompt and original OS media when
requested. This restores B with the revised five-row System font; the
original CGABASE blanking variant A is not part of this tester.
After a hang, boot plain DOS before restoring. To recover the exact pre-test
configuration, copy the saved SYSTEM.INI, WIN.INI and WIN.COM back from
UISAVE to WINDOWS; retain the full backup for other file recovery. A known
working 640x200 installation remains the fallback for larger dialogs.
There is no installer, automatic recovery, version recognition or DOS hash
check. Keep backups until the original configuration cold-starts normally.

What changes and the 100-line tradeoff
System cell/actual Windows text height increases from 5 to 6 pixels.
Capitals and digits have six ink rows; most lowercase gains a fifth ink row.
Character advances and horizontal dialog units stay unchanged. Windows
increases menu rows from 6 to 7 pixels and makes the tested dialog buttons
taller. Caption height stays at 8 pixels and accommodates the new face.
No custom USER patch or driver resource/timing edit is needed for this.
The small Save/exit-style test dialog fits. Actual Windows 3.0 Notepad Open
has its important OK and Cancel buttons fully visible, but its overall
height increases from 98 to 115 pixels: the bottom 15 pixels extend below
the 100-line screen. Do not expect every application dialog or lower list/
drive control to fit. Restore B or use 640x200 for those tasks. No generic
font-only change can promise larger text and unchanged dialog height.

Hardware comparison
Compare B and BIG on the SAME display and applications: titles, menus, a
short dialog, Notepad Open, mouse movement, repaint and return to DOS.
Please report whether larger strokes help through MCE2HDMI and on the LCD,
and whether any clipped controls prevent your usual work. Stop and restore
B if readability, flicker, snow, cursor/redraw or stability regresses.
The six-row font is an optional size/readability tradeoff, not a hardware
readability claim. Extended characters keep the original visible fallback
box where this tiny project font lacks a drawing; no Windows/ROM glyphs
were copied. No extra application fonts are installed.

Emulator scope
Windows 3.0 real mode, DOSBox-X 2025.02.01 CGA, 8086-prefetch, normal
640 KB, no EMS/XMS/UMB. Both fonts report actual height 5/6, ascent 5/6,
average width 3, dialog units 3x5/3x6, and 160x100. Native menu, title,
Save-style dialog and actual Notepad Open captures were compared. The tested
important buttons fit; Notepad's lower overflow is recorded above. Ordinary DOS Setup installed BIG, its cold start passed, then Setup restored
B and its cold start passed. The omitted grabber was obtained from original
OS media. Both close and return to DOS. Emulator checks cannot establish PPC512 hardware,
LCD contrast, MCE2HDMI scaling, physical snow or subjective readability.

Developer reproduction
Run Python 3 tools/PPCUI/BUILD.PY from this checkout to rebuild PPCUI.ZIP.
It reuses the committed exact B driver, current revised CG1 System face,
original fixed/OEM fonts and art. It generates only the font/Setup tester,
with no native driver rebuild or checksum/provenance manifests. Original
font source is tools/PPCUI/FONT.PY. The native smoke probe source is CHECK.C;
compile with MSC6 /G0 /Gw /AS and the existing project Win16 toolchain.

Native 160x100 previews beside this download: B5MENU.PNG / B6MENU.PNG
and B5DLOG.PNG / B6DLOG.PNG. These are Windows GetPixel captures, not
PPC512 photos or a simulation of MCE2HDMI/LCD scaling.
