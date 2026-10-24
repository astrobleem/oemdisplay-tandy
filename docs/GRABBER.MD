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

## Evidence (86Box Tandy 1000 HX, src/tgrab/TGSESS.PY)

`win` part, all exact:

- TGIMG.BMP (64x40, all 16 colours, asymmetric marker) opens in Paintbrush.
- Pick tool, Edit > Copy, File > New, Edit > Paste, Save As PASTE.BMP:
  the saved BMP holds the 64x40 picture at (0,0) with the original RGB
  colours, the rest white; reopening shows it exactly.
- Shift+PRINT: the Clipboard (saved by CLIPBRD as SCREEN.CLP) holds a
  320x200, 4-plane device bitmap equal to the screen in every pixel
  (except the parked pointer's corner).
- That capture pasted into a new Paintbrush image and saved: pixel-exact in
  the part Paintbrush pastes (its 262x126 drawing area at 320x200); the
  rest of the canvas stays white. That clipping is Paintbrush behaviour.

`dos9` part:

- TGPAT.COM draws the picture in BIOS mode 9. Alt+Tab to Windows and back:
  all 64,000 pixels restored with TANDYGR.GR2. With the retail CGA.GR2 the
  same run does not restore the screen (see the evidence folder).
- Shift+PRINT in mode 9 leaves the Clipboard unchanged (expected, below).

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
