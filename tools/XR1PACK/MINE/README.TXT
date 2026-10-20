MINESWEEPER FOR WINDOWS 3.0 REAL MODE

This package contains a converted WinMine executable and its tested About
helper. It does not include Windows, display drivers, fonts, or disk images.

INSTALL AND RUN
Start Windows 3.0 in real mode with the existing qualified XR1 launch
setup. Create C:\MINETST and copy WINMINE.EXE there. Copy WMABT.DLL to the
Windows SYSTEM directory; the verified path was C:\WINDOWS\SYSTEM\WMABT.DLL.
If a WMABT.DLL is already there, compare it with SHA256S.TXT. Save a backup
before replacing a different copy, and avoid keeping multiple competing
copies. To restore, close Windows and put the saved DLL back.

Use Start > Run in Tandy Start, or File > Run in Program Manager, and enter:
  C:\MINETST\WINMINE.EXE
Left click reveals, right click flags, F2 starts a new game, and Help > About
uses WMABT.DLL. Close the game and repeat the Run command to verify relaunch.

QUALIFICATION
This build has experimental emulator qualification for Windows 3.0 real
mode, the tested SYSTEM placement, game launch/About/basic play, DOS return,
and direct-driver panning of the Beginner board. See QUALIFY.JSN for records
and limits. Physical Tandy/XT operation and automatic XTPAN edge-follow are
not qualified; complete Expert-board panning is also unqualified. A 640x200
display may clip the lower board.
