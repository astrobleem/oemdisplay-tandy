# WindowsXT splash-only updater 0.2 qualification

The shipped updater changes the appended startup image in a recognized
`WIN.COM`, preserving its entire 4,336-byte configuration/loader prefix.
It does not rerun Setup or replace any Trial4 driver, font, INI, or shell.
Only exact stock, old-Tandy and approved-result hashes are accepted.

## Completed checks

- Primary host suite: 1,048 state/refusal/repeat/corruption cases; the portable
  published harness was rerun against the qualified source/runtime inputs.
- Independent review: 375 ASan/UBSan state cases, 120 process-interruption and
  I/O-failure cases (stock and old-Tandy originals), and 30 artwork-aware CHECK
  cases. No lost original or unrelated-file mutation was observed.
- Native DOS: 19 commands across nine apply/restore/idempotence/refusal and
  prepared interrupted-state scenarios, using 640 KB, normal core,
  `8086_prefetch`, fixed 200,000 cycles, and no XMS/EMS/UMB or FPU.
- Qualified DOS binary rebuilt byte-identically. A scoped linked MZ
  control-flow audit found no post-8088 suspects; it is not whole-system or
  physical-hardware certification.
- A copied optimized Trial4 `TR43216.DRV` installation retained all 107 other
  Windows files byte-for-byte immediately after applying; only `WIN.COM`
  changed and `WIN.WXB` appeared as the exact original.
- A new emulator process with only the installed C drive mounted displayed
  every approved splash pixel, reached Program Manager, and exited normally
  to DOS. That cold run used fixed 20,000 cycles and the same 640 KB/prefetch
  memory/CPU constraints. See `BOOT.PNG`, `DESKTOP.PNG`, and `EXIT.PNG`.
- The guard refused execution from an actual Windows 3.0 DOS application.
- Retained Trial4 fixtures using `TR41616.DRV`, `TR43216.DRV`, `TR43204.DRV`,
  `TR46404.DRV`, and `TR36402.DRV` share the recognized original startup file.
  The updater does not infer or alter their driver/font selections.

`BOOT.PNG` is an unedited 640x400 native capture: each 640x200 logical row is
doubled. It matches the approved artwork pixel-for-pixel, without aspect
correction or retouching. The 640x480 art preview is separate.

## Safety boundary

A verified original is renamed to an absent `WIN.WXB`; a verified stage is
then renamed into absent `WIN.COM`. RESTORE reverses those moves. No existing
file is opened for writing, overwritten or deleted. A partial/unknown stage
is preserved and blocks APPLY. RESTORE may recover an exact backup into an
absent live name while leaving an unknown stage untouched. No backup is
invented for an already-approved installation lacking an original.

Power loss, torn FAT/directory sectors, media/controller/cache failures, and
native DOS critical-error paths are not exhaustively verified. Injected
short writes, close failures and rename failures were host tests; native DOS
covered the documented recognized on-disk recovery states. The cycle settings
are not measurements of a physical Tandy. Actual cards and physical hardware
remain untested; run CHECK on the intended installation before APPLY.

The root historical OEM package and its pins are not changed by this folder.
Do not use an older OEM Setup disk as a Trial4 splash upgrade.

Exact accepted hashes, build identity and concise results are in `RESULT.JSON`
and the parent directory's `MANIFEST.SHA`. No Windows, driver, font, SDK,
toolchain, guest-disk image, or complete WIN.COM is included here.

## Repository text normalization

All published text uses CRLF. The qualified LF source was normalized without
semantic edits, rebuilt with the same C 6 flags, and produced a byte-identical
WXTSPL.EXE. The published CRLF source was also recompiled for the host and
passed all 1,048 portable safety cases; artwork tests passed again. RESULT.JSON
retains both source hashes so the earlier independent-review provenance is
explicit.
