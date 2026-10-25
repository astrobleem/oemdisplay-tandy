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
It does not run an emulator or prove Windows loader behavior. The DOS and
Win16 builds use Open Watcom `-0`; MINERUN targets Windows 3.0 and imports only
KERNEL and USER. `BUILD.JSN` records exact source, compiler and output identity.

Native acceptance is pending the coordinator's emulator allocation. Follow
the bounded [native checklist](../MINEAPP/NATIVE.MD). Do not publish these new
packets or replace current front-door URLs until that result is recorded.
Existing XR1/MINE and FullXT publisher inputs remain unchanged.
