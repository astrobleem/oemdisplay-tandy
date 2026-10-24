# Clipboard and DOS-program grabber, Tandy 320x200x16 (test candidate)

Status: emulator evidence only (86Box 6.0, Tandy 1000 HX machine; the
Windows XT `TR53216.DRV` unchanged). Not run on real hardware. The shipped
Windows XT disk, drivers, RESERVE and accepted hashes are unchanged; the
candidate is a separate Setup packet (`src/tgrab/TGPACK.PY`).

## Which component does what

| Operation | Component | Result |
| --- | --- | --- |
| Print Screen in Windows (whole screen to the Clipboard) | USER + display driver (`BitBlt` screen to a device bitmap) | works with the shipped `TR53216.DRV`, no change |
| Paintbrush Copy / Paste / Paste of a screen capture | Paintbrush + display driver | works, no change |
| Switching away from a full-screen DOS program and back | WINOLDAP + grabber (`SaveScreen` / `RestoreScreen`) | needed a grabber for the Tandy modes: `TANDYGR.GR2` |
| Print Screen inside a full-screen DOS program | WINOLDAP + grabber (`GetInfo`, `GetBlock`) | Windows 3.0 real mode copies **text screens only** |

The Tandy keyboard has no SysReq key: Print Screen is **Shift + PRINT**
(scan code 37h with Shift), which both Windows and WINOLDAP accept.

## TANDYGR.GR2

Built by `src/tgrab/BUILDTG.PY` from the Windows 3.0 DDK 286 CGA grabber
(pinned DDK view, nothing committed) with anchored edits, plus an unmodified
control build. The edits: mode from the BIOS data area (no light-pen
measurement), InfoContext entries for Tandy modes 8, 9, 0Ah, a 32 KB
graphics save area, refusal of unsupported modes (7, above 0Ah), and a mode
re-read before every grab. Size 2,255 bytes.

## Evidence (86Box Tandy 1000 HX, src/tgrab/TGSESS.PY; docs/tgrab)

Run `sA2` (TR53216.DRV, RESERVE, TANDYGR.GR2): 9/9 checks pass
(`docs/tgrab/sA2.JSN`, frames `A_*.png`).

- TGIMG.BMP (64x40, all 16 colours, asymmetric marker) opens in Paintbrush,
  all 2,560 pixels exact.
- Pick tool, Edit > Copy, File > New, Edit > Paste: anchored picture exact.
  Save As PASTE.BMP: the 64x40 picture at (0,0) with the original RGB
  colours, the rest of the 320x170 canvas white (`PASTE.BMP`); reopened:
  exact.
- Shift+PRINT: the Clipboard (saved by CLIPBRD as SCREEN.CLP) holds a
  320x200, 4-plane device bitmap equal to the screen in every pixel except
  the parked pointer's corner.
- That capture pasted into a new Paintbrush image and saved: pixel-exact in
  the part Paintbrush pastes (its drawing area at 320x200), the rest white.
- TGPAT.COM in BIOS mode 9; Alt+Tab to Windows and back: all 64,000 pixels
  restored. Shift+PRINT in mode 9 leaves the Clipboard bitmap unchanged.

Run `sB` (same, retail CGA.GR2): the mode-9 program comes back in a CGA
4-colour mode with a scrambled picture (`B_dos9_after_cgagr2.png`).

Run `sC` (TANDYGR.GR2, RESERVE) text grab: Windows stops answering
(`C_text_after_grab_reserve.png`, limitation 2). Control without RESERVE
(Microsoft CGA.DRV, TANDYGR.GR2, otherwise the same machine): the Clipboard
holds the DOS text (`D_text_clip_noreserve_cgadrv.png`). TR53216.DRV itself
does not start without RESERVE, so that control cannot use it.

Install: the packet's OEMSETUP.INF gives one Setup choice. The tested
installation has exactly the result of that choice (SYSTEM.INI
`286grabber=TANDYGR.GR2`, the file in WINDOWS\SYSTEM, the unchanged
driver). Choosing it through Windows Setup inside Windows was not completed
in the emulator: at 320x200 Setup's display list cannot be opened from the
keyboard or mouse (the dialog is wider than the screen).

## Limitations

1. **No DOS graphics screens on the Clipboard in Windows 3.0 real mode.**
   WINOLDAP's grab code continues only when the grabber's `GetInfo` returns
   1 (text screen), and the module imports no GDI bitmap-creation function
   (its only GDI import is ordinal 154), so it can only place OEM text on the
   Clipboard. No grabber change can add graphics capture; it would need a
   different WINOLDAP (standard/386 mode needs a 286/386).
2. **Text capture from a DOS program fails while RESERVE is loaded.** After
   Shift+PRINT in a text-mode DOS program and returning to Windows, Windows
   stops answering input (hourglass; keys are consumed by a DOS console
   read). Reproduced with TR53216 and with Microsoft's CGA.DRV, with
   CGA.GR2 and TANDYGR.GR2, in 86Box and DOSBox-X. Without RESERVE, or
   with an equal 18 KB block resident low in memory instead, the same grab
   works and the Clipboard holds the text. The trigger is RESERVE's
   allocated block at the top of the DOS arena; the exact failing operation
   inside WINOLDAP is not yet identified. Avoid DOS text capture with the
   Tandy drivers until this is fixed.
3. Palette changes made by a DOS program through the Tandy palette
   registers, or CRT page changes outside the BIOS, are not saved; the BIOS
   mode set on restore gives the default palette and pages.
4. The 32 KB save area costs 16 KB more memory per switched-away graphics
   DOS program than CGA.GR2.
