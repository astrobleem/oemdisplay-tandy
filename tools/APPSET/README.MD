# Portable native app packets

This builder is scoped to Cookie and the Windows 3.0 Minesweeper packet.
It preserves the accepted application/shim bytes. No installed Windows,
display, sound, INI, shell or boot file is modified by either installer.

`COOKSET.EXE` and `MINESET.EXE` are DOS 3.20+ / 8088 self-extracting programs.
They need no external unpacker. Their fixed, compiled flat member list is
size/CRC checked before output. Matching destination files are reused; a
different existing app file is refused before any copy. Copy/readback uses a
new temporary file and rename, so a failed write or abandoned temporary file
does not overwrite a real file or prevent the next ordinary install attempt.
Cookie saves and other unrelated destination files are left alone.

Minesweeper uses `MINERUN.EXE` inside the user's already running Windows 3.0
real-mode desktop. That launcher validates and loads the bundled private
`WMABT.DLL` by full path before `WinExec` starts the accepted `WINMINE.EXE`.
The loader holds its DLL reference until `WinExec` returns, then releases it;
the game's normal import owns its reference. A different module already
loaded under the same name is left alone. No global DLL install/restore
machinery is needed. Cookie already runs as a standalone native Windows app.

Developer build only, with the explicitly supplied installed toolchain:

```text
python tools/APPSET/PACK.PY --watcom C:\WATCOM --out NEWBUILD
python tools/APPSET/TEST.PY --build NEWBUILD --out NEWHOST
```

The host suite invokes the required GCC wrapper and uses process-local runtime
paths. It checks extraction, retries, collisions, damaged archives, disk-full
cleanup, saved-game preservation, and private-loader success/refusal/release.
The DOS backend mock assigns raw handles outside the CRT descriptor range;
it catches accidental mixing of `_dos_creatnew` with CRT write/close.
It does not run an emulator or prove Windows loader behavior. The DOS and
Win16 builds use Open Watcom `-0`; MINERUN targets Windows 3.0 and imports only
KERNEL and USER. `BUILD.JSN` records exact source, compiler and output identity.

The bounded native normal flow passed on 2026-10-25: 386 seconds, 10 checks,
8088 / 640 KB / MS-DOS 6.22 / guarded Windows 3.0 real mode. Both SFX installers
and matching retries ran in DOS. Minesweeper launched/About/closed twice with
only the app-local DLL; Cookie click/buy/save/load/exit and preservation of its
save through a DOS reinstall passed. SYSTEM.INI and CONFIG.SYS were unchanged.
See [NATIVE.JSN](NATIVE.JSN) and the [scope/procedure](../MINEAPP/NATIVE.MD).
The separately owned unified SOUND release was not imported into this fixture.

`TESTPKG.PY` is a read-only standard-library source/packet regression check. It
requires exact native-qualified artifact bytes and the pinned execution logs.
A rebuild with different app bytes loses that recorded pass automatically.
The GitHub workflow runs this check; no compiler or emulator is needed there.

Driver packet builders may define `APP_READY(where)` in their generated
FILES.H to print their own plain-DOS completion instruction. The default is
unchanged. All four app packets are byte-identical with this source hook.
This hook does not qualify another packet's installer or consumer path.

Publication/front-door updates remain a separate release step. Existing
XR1/MINE and FullXT publisher inputs remain unchanged.
