XTEyes 1.0 - Windows 3.0 / 8088
================================
A small pair of eyes that follows the mouse. Original Win16 implementation,
inspired by classic xeyes and Michael Duerr's WinEyes:
https://github.com/michaelduerrwhiteduck/WinEyes

WinEyes is a modern C#/WPF application targeting .NET 9. This is a new
implementation for Windows 3.0 real mode, not a binary/source-compatible port.
No WinEyes code or artwork was reused. Its MIT notice is included for reference.

RUN
Copy the XTEYES folder anywhere on the Windows machine, for example
C:\WINXT\XTEYES alongside the optional suite. Run XTEYES.EXE from
Program Manager's File > Run, or the Tandy Start Run box. No installer, DLL,
INI change, or shell replacement is needed. The EXE is self-contained.
Move by dragging the title bar. Minimize with the title-bar arrow. Close using
the system menu or Alt+F4. About is in the system menu (Alt+Space).
It is a normal window, not forced on top. It has no transparent desktop mode.

DESIGN
- Microsoft C /G0 target: 8086/8088 instructions, no coprocessor required.
- Windows GDI only. No hardware video memory, global hooks, or direct port I/O.
- One 125 ms timer: nominal maximum 8 pointer polls/second. Windows scheduling
  and 8088 load may reduce the actual rate; this is not a measured 8 FPS claim.
- Integer bounded pupil motion. A conservative diamond-shaped travel region
  keeps the full pupil rectangle inside the eye; no floating point or sqrt.
- Monochrome bitmap artwork avoids the driver's slow ellipse drawing path.
- Pointer movement erases only the old pupil rectangle and blits the new pupil.
  Stationary pointers cause no drawing. Minimized, invisible, entirely
  off-screen or fully clipped windows skip tracking work.
- Exposure repaints the eyes and current pupils using clipped BitBlt calls.
- Uses stock white brush plus two owned bitmaps and two memory DCs. Owned
  objects are deselected and released on exit, including partial setup failure.
- Black/white artwork is suitable for all five supported Tandy driver modes.
  Native validation covers 160x200, 640x200 monochrome, and Trial4 320x200x16.
  The other two modes have not been separately run in this test pass.
- The small-mode title bar enforces Windows' minimum window width; artwork
  is centered. The window still fits within the 160-pixel-wide desktop.

VALIDATION
See TESTS.TXT and EVIDENCE for native emulator results and real screenshots.
These are Windows 3.0 real-mode tests with 640 KB, no XMS/EMS/UMB, no FPU,
and DOSBox-X's four-byte 8086_prefetch core (its 8088-compatible setting).
No physical Tandy performance measurement has been made.

SOURCE / BUILD
SOURCE contains XTEYES.C, EYES.H, XTEYES.DEF, XTEYES.RSP and BUILD.BAT.
The artwork is included as original one-bit C arrays; no resource compiler.
Use the established Microsoft C/Win3 SDK toolchain on C: with BIN, LIB,
INCLUDE, DDK\286\INC. Place source on D:, run BUILD.BAT. The flags are:
  CL /nologo /c /G0 /Gw /AS /W3 /Od XTEYES.C
  LINK4 /NOE /NOD @XTEYES.RSP
No compiler, Windows installation, display driver or proprietary SDK files
are distributed. Evidence includes compiler log and scoped instruction audit.
QA source and host geometry check are in TESTSRC; these are not needed to run.

LICENSE
Original XTEyes code and artwork: MIT, see LICENSE.TXT.
Reference WinEyes notice: WINEYES.TXT (unmodified upstream placeholder notice).
