# Clipboard and DOS programs, Tandy 320x200x16 (test candidate)

Status: emulator evidence only (86Box 6.0, Tandy 1000 HX machine, the
Windows XT `TR53216.DRV` unchanged). Not run on real hardware. The shipped
Windows XT disk, drivers, RESERVE and accepted hashes are unchanged; the
candidate is a separate packet (`src/tgrab/TGPACK.PY`).

## Which component does what

| Operation | Components | Status |
| --- | --- | --- |
| Print Screen in Windows | USER + display driver | works with the shipped `TR53216.DRV`, no change |
| Paintbrush Copy / Paste | Paintbrush + display driver | works, no change |
| Switching away from a full-screen DOS program and back | WINOLDAP + grabber Save/RestoreScreen | **new grabber `TANDYGR.GR2`** (CGA.GR2 scrambles modes 8-0Ah) |
| Print Screen in a DOS text program | WINOLDAP + grabber GetBlock | works; with RESERVE it hung Windows: **fixed by `TGEVEN.COM`** |
| Print Screen in a DOS 16-colour graphics program (modes 8, 9) | grabber GetInfo/GetBlock + Windows-side consumer | **new**: `TANDYGR.GR2` writes a BMP, **`TGCLIP.EXE`** puts it on the Clipboard as a bitmap |

Print Screen on the Tandy keyboard is **Shift + PRINT** (scan code 37h
with Shift), which Windows and WINOLDAP both accept.

## DOS graphics screens to the Clipboard

The DDK grabber interface does describe graphics grabs (`GetBlock` with
`FMT_OTHER`, `GT_NEWBITMAP` records). The consumer in Windows 3.0 **real
mode** (`WINOLDAP.MOD`, the only mode an 8088 runs) does not use them:

- its DOS-side grab routine continues only when the grabber's `GetInfo`
  returns 1 (text screen);
- the Windows side reads the record from its grab file and calls
  `SetClipboardData` with `CF_OEMTEXT` for text; for any other record type
  it passes a pointer value as the format; its only GDI import is ordinal
  154, so it cannot create a bitmap.

So the capture is implemented in two parts of our own, without changing
WINOLDAP:

1. **`TANDYGR.GR2`**: `GetInfo` reports modes 8 and 9 as grabbable.
   `GetBlock` (called by WINOLDAP with DOS idle, just before it writes its
   own file) writes the screen as a 4-bit BMP: rows bottom-up, each Tandy
   IRGB nibble translated to the Windows device index (bits 0 and 2
   swapped), palette = the display driver's colour table. The file goes to
   `%TEMP%\TANDYGR.BMP` (else the root of the current drive), and WINOLDAP
   gets one text line: `TANDYGR <path>`.
2. **`TGCLIP.EXE`** (Windows, C, 5 KB): a Clipboard viewer. When that line
   arrives it reads the BMP, `CreateDIBitmap`s a device bitmap, replaces the
   Clipboard contents with it (`CF_BITMAP`) and deletes the file. Run once,
   it adds itself to WIN.INI `load=`.

## The text-grab hang with RESERVE, and TGEVEN

KERNEL places the global heap's end sentinel at `(end - 1) AND 0FFFEh`
(GlobalInit, `KERNEL.EXE` code segment 1 offset B42Fh). RESERVE puts its
block header at 97FFh, so the free block Windows takes ends at 97FFh (odd)
and the sentinel is the block's **last paragraph** (97FEh); without RESERVE
the end is 9C00h and the sentinel is 9BFEh. A full-screen DOS program run
from Windows gets the memory up to that end, and WINOLDAP does not put the
sentinel paragraph back (DOSBox-X memory dumps: valid `Z` sentinel at
97FEh on the desktop, zeros after a DOS session). The next walk of the
heap that reaches the end loops for ever; the first one after a text grab
is the Clipboard allocation, so Windows stopped answering.

Isolating it: a generic TSR that allocates a high 16 KB block the same way
reproduces the hang; a low block of the same size does not; a 1-paragraph
guard (end stays odd) does not help; a 2-paragraph guard (end even) fixes
it. `TGEVEN.COM` (run right after RESERVE) allocates exactly that guard at
the top of the largest free block when its end is odd, keeps only its PSP
resident (304 bytes in all), never edits an MCB, and does nothing when the
end is already even. RESERVE itself is unchanged. The packet's
`TGSTART.BAT` is the Windows XT launcher with that one step added.

## Installing the packet

Windows 3.0 DOS Setup, Display > Other (disk from the manufacturer), path
of the packet: Setup lists the packet's one entry ("Tandy EX/HX 320x200 16
colors, Tandy grabber (TEST)", `L_list.png`), copies the files and writes
`display.drv=TR53216.DRV` and `286grabber=TANDYGR.GR2` to SYSTEM.INI. Run
on 86Box (fresh install into a new directory, `L_*.png`): the installed
`TANDYGR.GR2` and `TR53216.DRV` are byte-identical to the packet's (SHA-256
`29f85af5...`, `33f681b0...`), and the Setup GUI itself ran on
`TR53216.DRV`. Setup does not copy TGEVEN, TGCLIP or TGSTART.BAT: copy them
from the packet to the Windows directory, start Windows with TGSTART.BAT
and run TGCLIP once (it then adds itself to `load=`).

## Evidence (86Box Tandy 1000 HX, `src/tgrab/TGSESS.PY`, `docs/tgrab`)

Run `sG` (TR53216.DRV, RESERVE + TGEVEN, TANDYGR.GR2, TGCLIP): every check
in one session, see `sG.JSN` and the `G_*.png` frames.

- Self-test (host): the BMP colour check passes the original picture and
  fails a changed palette entry and a changed pixel. All BMP checks compare
  each pixel's colour with the reference palette (`TGIMG.WINPAL`), not
  with the saved file's own palette.
- TGIMG.BMP (64x40, all 16 colours, asymmetric marker) shown exactly;
  Pick, Copy, New, Paste: exact; saved PASTE.BMP: exact colours, rest
  white; reopened: exact.
- Shift+PRINT in Windows: Clipboard bitmap 320x200, 4 planes, equal to the
  screen; pasted and saved: exact in the part Paintbrush pastes.
- TGPAT.COM (mode 9): exact; Alt+Tab away and back: all 64,000 pixels.
- Shift+PRINT in mode 9: the Clipboard holds a 320x200 bitmap equal to the
  DOS screen in every pixel (saved by CLIPBRD as DOS9.CLP); pasted into
  Paintbrush and saved as DOS9.BMP: the picture at (128,80) in the reference
  colours, black around it.
- Text: COMMAND.COM, ECHO line, Shift+PRINT, EXIT: Windows answers and the
  Clipboard holds the line (TEXT.CLP).

Controls: `sF` (same, **without** TGEVEN): the text check fails (Windows
stops answering). `sB` (retail CGA.GR2): the mode-9 program comes back
scrambled (`B_*.png`).

## Limitations

1. Graphics capture covers the 16-colour modes 8 and 9. CGA modes 4-6 and
   Tandy 0Ah keep the DDK behaviour (not copied).
2. Paintbrush pastes only what fits its drawing window (262x126 at
   320x200); the Clipboard bitmap itself is the full 320x200.
3. Without TGCLIP running, a mode-8/9 Print Screen leaves the text line
   `TANDYGR <path>` on the Clipboard and the BMP in TEMP.
4. TGEVEN must run after RESERVE and before Windows (TGSTART.BAT); the
   shipped TSTART.BAT does not run it.
5. A DOS program's own Tandy palette or CRT-page changes made outside the
   BIOS are not saved or captured (default palette assumed).
6. The 32 KB save area costs 16 KB more than CGA.GR2 per switched-away
   graphics program.
