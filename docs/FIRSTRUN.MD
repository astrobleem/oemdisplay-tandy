# Windows XT first-run update

This update addresses the six first-run reports in the fresh Windows XT disk.
All five TR5 graphics drivers, the experimental text driver, approved splash,
and TSINPUT.DLL retain their previous hashes. Existing rc.1 downloads remain
unchanged. Supply your own matching Windows 3.0 support files.

| Report | Change | Evidence |
| --- | --- | --- |
| Second disk prompt defaults to C:\WINDOWS | TINST preserves OEMSETUP.INF as OEMBASE.INF and writes the actual source path into its disk entry; the launcher also selects that source drive/directory. | Unchanged released files reproduce the exact bad default and repeated Enter failure. Real Setup completes at C:\WINXT and C:\XTALT, with matching driver/font hashes and the approved WIN.COM splash result. |
| TR5 Clock jargon | Remove the optimization label from all five graphics Setup choices. | Actual Setup shows the clean Tandy resolution/color description. Driver/profile bytes are unchanged. |
| Backup disappears; next steps unclear | Pause after verified backup output; print actual rollback/launch paths and the optional TSSETUP command when its supported C:\WINXT/C:\WINDOWS layout applies. Fresh recovery says no recovery is needed. | Generated-path/guarded DOS fixtures, actual installer logs and source review. Alternate layouts receive their actual launcher path. |
| E does not select Exit | Use &Exit; explicitly keep Cancel as the initial focus/default. | Built-in AUTOTYPE reaches the real production dialog. Enter and Escape cancel with the shell still running; a later E produces normal Windows shutdown. Passive logs show focus/default ID 2. |
| DOS prompt overlaps moon | Reserve four blank rows below the artwork; separator moves to row 20 and cursor returns at row 22. | Exact renderer BIOS simulations are in CI. Full closing video with the subsequent DOS prompt remains a manual check. |
| Apps missing from Programs | Add a bounded Windows XT group from [Programs] in Windows TSHELL.INI. Existing executable paths only appear; Matrix/Maze/Starfield use /S, About and Pinball v2 are configured. TP/Tandinator appear only when separately supplied. | Production-function host tests cover missing/bad/long paths, exact arguments, count limits and gaps. Native capture shows the extra group beside the original three. Full group/app-launch replay is still pending. |

[Machine-readable native observations](FIRSTRUN/RESULT.JSN),
[original bad disk prompt](FIRSTRUN/BEFORE.PNG),
[period compiler log](FIRSTRUN/BUILD.LOG),
[matching media-helper build](FIRSTRUN/PREPBLD.LOG),
[Enter cancellation](FIRSTRUN/ENTER.LOG) and
[Escape cancellation](FIRSTRUN/ESCAPE.LOG) retain the measured scope.

The tests use disposable clones, normal 640 KB and 8086 semantics, with no
installed Windows/CF changes. Built-in DOSBox-X AUTOTYPE supplies input;
the observer reads dialog state and sends no keyboard/mouse input. Some
longer scripted runs timed out and are recorded as incomplete, never passes.

These are functional emulator checks. Cycles are not calibrated hardware
speed. The bundled Pinball is pinned to merged PR 113; its EX-speed acceptance
remains pending separate work. No claim of physical Tandy performance is made.

The public disk is a 720 KB FAT12 data image with 43,008 bytes free and no
Windows support files, fonts, OS installation or private compiler/toolchain.
PREPXT stages matching owned files to a fresh writable C:\WINXT. Never run
WINXT\INSTALL directly from a small/read-only floppy. The original source
INF is retained as OEMBASE.INF once the guarded installer localizes it;
MANIFEST.SHA describes original release media, not the generated installed INF.

After successful Setup: run C:\WINXT\TSSETUP for the optional desktop, then
C:\WINXT\WINXT. Existing shell/settings files are refused, never overwritten.
For rollback use the exact numbered backup's RESTORE YES at real DOS.

Before calling remaining interactive checks complete, verify Programs launches
(including /S wake behavior and Pinball), Enter/Escape/E in other modes, and the
full moon-to-DOS-prompt closing sequence. Physical GoTek, real input devices,
calibrated EX-speed behavior and hardware acceptance remain separate.

Final native media/interactive replay is paused while the user's hub DOSBox
is active. The frozen public image passes independent geometry, exact-file,
helper-pin and checksum verification; no pending native run is called a pass.
