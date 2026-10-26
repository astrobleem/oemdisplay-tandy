# Tandy grabber integration acceptance

The normal expanded package passed native DOS preparation (375 fresh files and
87 update files, all compared with the current closed recipes), full FIXXT
installation and CHECK /VERIFY, and ordinary Windows Other display selection.
The selected HPXY driver retains TANDYGR.GR2 and the TGCLIP startup helper
through normal DISPWIN startup. No separate TGSETUP step is required.

DOS text Clipboard capture passed. A real mode-9 DOS picture was verified in
video memory before capture; all 64,000 Clipboard pixels matched an independent
BIOS palette reference. The visible Paintbrush paste matched an independent
250 by 169 pixel region.
A separate focused exit check returned Windows normally to DOS. The Save As
automation did not produce its requested file; that harness failure is
preserved and is not counted as acceptance evidence. INSTALL.ZIP preserves
the raw
successful evidence and earlier harness failures with their actual scope.
PACKAGE.JSN binds the exact tested archive, source inventory and raw evidence.

The grabber and TGCLIP reproduce the earlier FA/FB/FC runtime bytes exactly;
those records retain the broader original grabber and full-picture workflow
proof. The HPXY driver and original CGA grabber bytes remain unchanged.
BUILD.JSN records compiler reproduction and 61 host checks.

These checks used emulated Tandy EX/HX hardware with an 8088 and normal 640 KB.
They do not claim physical-hardware qualification or recovery of palette writes
made directly to write-only hardware ports. Publication requires separate approval.
