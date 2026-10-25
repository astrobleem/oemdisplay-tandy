# Native app normal-flow qualification

The bounded acceptance passed on 2026-10-25 in 386 seconds. [NATIVE.JSN](../APPSET/NATIVE.JSN)
binds both EXE/ZIP pairs, the actual guest logs and the exact scope. The private
fixture used an emulated Tandy 1000 HX, 8088 at 7.159092 MHz, 640 KB, no dynarec,
MS-DOS 6.22 and Windows 3.0 real mode. This is not physical hardware evidence.

Both complete DOS SFX installers extracted every pinned member exactly into new
folders. Matching MINESET retry passed before Windows. The fixture retained its
normal `C:\STARTXT.BAT` / WINXT / XTCLEAN / XTTEST route and TSHELL desktop, with
HPXY.DRV and stock SOUND.DRV. Neither Windows nor SYSTEM contained WMABT.DLL.

A developer-only extra WIN.INI load task, [APPQA.C](QA/APPQA.C), waited for the
normal shell before launching the apps through WinExec. It did not replace the
shell or depend on WIN application-command-tail forwarding. MINERUN loaded the
private DLL at `C:\MINETST\WMABT.DLL`; the controller verified the module path,
opened the owned Help / About dialog, requested a new game and closed normally.
A second complete launch/About/close cycle passed. This verifies the Win16 DLL
reference lifetime after MINERUN exits. It does not claim manual File/Run input.

Cookie ran directly from the same desktop. Click/buy produced a valid one-CPS
save; New/Load/Save restored that state, and the app closed normally. Windows
returned normally to DOS. A COOKSET retry preserved COOKIE.SAV byte for byte.
All packet members still matched. No global shim or staging temporary remained;
installed SYSTEM.INI and CONFIG.SYS matched their pretest bytes. The controller's
own startup/task setup is separate from the product's unchanged configuration.

The 60-check host suite covers both CRT and raw DOS backends, all-collision
preflight, corruption/refusal, disk-full cleanup/retry, foreign-file/save
preservation and private-launcher error cleanup. Its offset-handle mock catches
the mixed raw-DOS/CRT regression found in the first failed native extraction.
These error cases were not additional native runs in this bounded window.

DOS 3.20+ remains the code target; the actual native OS tested was MS-DOS 6.22.
The separately owned unified SOUND release was not imported. No claim is made
about that unpublished integration or a new physical-hardware matrix.

To repeat the normal check, obtain a direct coordinator slot and byte-0 lease,
clone a stopped accepted Windows fixture privately, run both SFX installers and
matching retries, then use the normal guarded desktop with APPQA as an extra
load task. Keep Windows/DOS media and raw images private. Record packet hashes,
actual app logs and the bounded result; verify stop/release for owned children.
The passing artifact bytes need no repeat solely for completion-hook source
changes that rebuild to these exact same bytes.
