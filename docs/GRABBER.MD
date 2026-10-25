# Clipboard and DOS programs on the Tandy 1000 (test candidate)

Status: emulator evidence only (86Box 6.0, Tandy 1000 HX machine). Not run
on real hardware. Nothing in `distributions/WINXT` changes: the shipped
drivers, RESERVE, launcher and accepted hashes are as released. The
candidate is a separate packet (`src/tgrab/TGPACK.PY`) installed from DOS.

## Install and use

At a plain DOS prompt, with the packet on a floppy (or any folder):

    A:
    TGSETUP

`TGSETUP.EXE` checks every packet file (size and CRC-32, `TGSETUP.LST`),
keeps the original `SYSTEM.INI` and `WIN.INI` in `C:\WINDOWS\TGBAK` once,
copies `TANDYGR.GR2` to `C:\WINDOWS\SYSTEM` and `TGCLIP.EXE` to
`C:\WINDOWS` (written as `.NEW`, read back, renamed), sets
`[boot] 286grabber=TANDYGR.GR2` and adds `C:\WINDOWS\TGCLIP.EXE` to
`[windows] load=`. Every other INI byte is kept. Windows is then started
the usual way (`C:\WINXT\WINXT`); the launcher, `CONFIG.SYS` and
`AUTOEXEC.BAT` are not touched. `C:\WINDOWS\TGBAK\TGSETUP /REMOVE` puts
the previous grabber back and takes TGCLIP out of `load=`. TGSETUP refuses
inside Windows, on a damaged packet, and while an XTMODE mode change can
still be undone (`XTMODE.JRN`: run MODES first).

Print Screen on the Tandy keyboard is **Shift + PRINT**.

| Where | Result |
| --- | --- |
| Windows | whole screen as a bitmap (USER and the display driver, unchanged) |
| DOS text program | the text (WINOLDAP) |
| DOS graphics program, modes 4, 5, 6, 8, 9, 0Ah | the picture as a bitmap, in the colours shown (TANDYGR + TGCLIP) |

Paintbrush pastes only what fits its window. For a whole picture its own
workflow is: Options > Image Attributes, the picture's size in pels; File
> New; View > Zoom Out; Edit > Paste; click outside the picture to place
it; View > Zoom In; save.

## Components

**`TANDYGR.GR2`** is the Windows 3.0 DDK 286 CGA grabber (`BUILDTG.PY`,
anchored edits; an unmodified control build is made alongside) plus three
modules of ours:

- `TGTANDY.ASM` - InitScreen, the palette shadow and the pixel-to-colour map.
- `TGSRSCR.ASM` - Save/RestoreScreen, Enable/DisableSave, SetSwapDrive.
- `TGBMP.ASM` - GrabBmp, Print Screen of a graphics mode to a 4-bit BMP.

It adds:

- Tandy modes 8, 9 and 0Ah in the mode table (CGA.GR2 indexes past its table for them).
- Saving and restoring every graphics mode when switching away. The screen
  goes to a temporary file in WINOLDAP's swap directory, else `%TEMP%`.
  The file is deleted on restore. A session's save area is therefore the
  text size (about 4.3 KB) instead of 16 KB (CGA.GR2) or 32 KB.
- Print Screen in every graphics mode. GetInfo reports the screen
  grabbable, since real-mode WINOLDAP grabs only when GetInfo returns 1.
  GetBlock writes the screen as a 4-bit BMP and hands WINOLDAP one text
  line, `TANDYGR <path>`. Every BMP pixel is the Windows device index of
  the colour on screen:
  - 8, 9, 0Ah: palette register[p];
  - 4, 5: the CGA colour code from `0:466h` (and the B/W bit), through the palette registers;
  - 6: register 0, and register[`0:466h` AND 0Fh].
- The heap's last paragraph (below).

**`TGCLIP.EXE`** (Windows, C) is a Clipboard viewer started from `load=`.
When the `TANDYGR <path>` line arrives, it reads the BMP, creates a device
bitmap with `CreateDIBitmap`, replaces the Clipboard contents with it
(`CF_BITMAP`) and deletes the file. The real-mode WINOLDAP, the consumer,
sets only `CF_OEMTEXT` and imports no bitmap GDI calls.

## Colours: what can be captured

The Tandy video array (port 3DAh index, 3DEh data) is write-only. The Tandy
1000 HX BIOS (v02.00.00) programs it for INT 10h AH=00h, 0Bh and 10h
without keeping a copy (disassembly: F000:F94D-FA2B, E55A-E615, F746-F7E7).

So TANDYGR keeps its own copy. InitScreen hooks INT 10h, but only in the
DOS session's vector table: INT 21h must belong to the caller, which is
WINOLDAP's DOS side. WINOLDAP saves that table when it switches to Windows
and restores Windows' own, so the hook never runs in Windows. The hook
repeats on the copy what the BIOS does:
- the mode-set palette: identity; 640x200x4 is 0, 3, 5, 15; the monochrome table when `0:4B4h` = FFh;
- background and palette select (AH=0Bh);
- one register, the border, or all registers (AH=10h AL=0, 1, 2), including the BIOS's register remap in modes 4, 5 and 6.

The copy is kept in the save area with the screen and loaded into the
registers again after switching back.

A program that writes the registers with OUT instructions cannot be
observed: an 8088 cannot trap port writes, and the registers cannot be
read back. Such a screen is copied, and restored after ALT+TAB, in the
colours of the last BIOS setting. The tests show this exactly: the grab
equals the palette-0 screen, not the screen. If no INT 10h mode set was
seen, the BMP header's reserved word says `TA` (BIOS default assumed)
instead of `TK`.

The CGA colour select (`3D9h`) comes from `0:466h`, which the BIOS keeps.
A direct OUT to 3D9h is likewise invisible.

## The heap's last paragraph (the old text-grab hang)

KERNEL puts the global heap's end sentinel at `(end - 1) AND 0FFFEh`
(GlobalInit, `KERNEL.EXE` code segment 1 offset B42Fh). With RESERVE the
heap ends at 97FFh (odd), so the sentinel is the heap's very last
paragraph. WINOLDAP does not carry that paragraph between Windows and the
DOS program. COMMAND.COM's transient part overwrites it, and the next walk
of the heap loops for ever. The first such walk is the Clipboard
allocation of a text grab.

TANDYGR handles that one paragraph itself, from the layout it finds:
- **EnableSave** (program starts): the DOS block holding the grabber is
  followed by the free block the program gets, and that block's end is the
  heap's end. If the end is odd and there is a `Z` arena header there, the
  grabber keeps Windows' 16 bytes.
- **SaveScreen** (switching to Windows): keeps the program's 16 bytes and
  puts Windows' back.
- **RestoreScreen**: the reverse, taking Windows' bytes as they are now.
- **DisableSave** (program ended): puts Windows' back.

With an even end, or anything unexpected, nothing is touched. Nothing is
allocated, and nothing stays resident when Windows exits. So repeated
launches, an already-loaded RESERVE and other layouts need no handling,
and the launcher is unchanged. This replaces the earlier `TGEVEN.COM`
guard, which needed a launcher step.

## Evidence

All runs are `src/tgrab/TGFLOW.PY` on 86Box Tandy 1000 HX. Results are in
`docs/tgrab/F*.JSN`, frames are `docs/tgrab/F*_*.png`, and saved BMPs are
in `docs/tgrab`.

The base system is Windows 3.0 with the Windows XT files in `C:\WINXT`
(`distributions/WINXT/STAGE.PY`). The kit's `INSTALL` refuses this
emulator's Windows media: CPSET requires `SETUP.INF` = 49,046 bytes, and
this copy has 49,095. So the launcher `WINXT.BAT` was written from TINST's
own template (`src/tandysw/TINST.C` lines 303-327, for `C:\WINXT` and
`C:\WINDOWS`). The real `WAVEXT APPLY` was then run on DOS: every launch
goes through `C:\WINXT\WINXT`, `XTMODE`, `RESERVE`, `WAVEXT START`,
`XTCLEAN.COM` and `XTTEST.COM /R`, which is the default wave path.

Test-only additions, never in the packet:
- `C:\TGT\TGCLOG.EXE` in `load=`: it records every Clipboard change (the
  bitmap via GetBitmapBits, the text) and Windows' free memory.
- `TGFREE.COM`: the largest free DOS block.
- `TGHIGH.COM n`: occupies n paragraphs below RESERVE, to change the layout.
- PATH with `C:\WINXT;C:\TGT`, because the 86Box keyboard map loses typed spaces and backslashes at the DOS prompt.

RESULTS_PLACEHOLDER

## Limitations

1. Emulator only; no run on a real Tandy 1000. 86Box's 640x200x4 rendering
   is marked "a guess" in its source, so mode 0Ah is checked against
   86Box's interpretation (even byte = bit 0 of eight pixels, odd byte =
   bit 1).
2. Colours set with OUT instructions instead of the BIOS (above).
3. CRT/CPU page changes (port 3DFh) are not followed. The grabber reads
   and saves the CPU page at B800h, which is the displayed page unless a
   program separates them.
4. Without TGCLIP running (for example after removing it from `load=`), a
   graphics Print Screen leaves the line `TANDYGR <path>` on the Clipboard
   and the BMP in TEMP.
5. XTMODE (MODES) and Windows Setup select CGA.GR2 again when they change
   the display. Run TGSETUP again afterwards.
6. Switching away from a graphics program needs room for a 16 or 32 KB
   temporary file. Without it WINOLDAP stays in the program (beep), as
   with the EGA grabbers.
