# Native consumer installers

XSETUP is the DOS 3.20+ / 8088 preparation and Setup front end for XRSYNC.
Consumers use the prebuilt XRSYNC.EXE download on their DOS computer.
It reads the public stored ZIP or its own appended ZIP, gathers the matching
installed Windows support locally, validates CRCs and readback, and hands
installation to normal Windows Setup. RUNSYNC uses its installed-file check.
No Windows bytes, toolchain, emulator or disk image is distributed here.

Developer rebuild only:

```text
python tools/DOSINST/BUILD.PY --watcom C:\WATCOM --out NEWBUILD
```

Open Watcom's 16-bit DOS compiler uses `-bt=dos -0 -ml -os`; BIN/XSETUP.EXE
is the tested prebuilt helper. XSNATIVE.JSN binds its exact build inputs.
The runtime driver remains the qualified PR155 XRSYNC.DRV. Public packet
construction and checks live in tools/XRSYNC/PUBLISH.PY and TESTPKG.PY.
The retained Python preparation script is developer reference tooling and
is absent from the consumer download.

[Actual DOS installation results](../../docs/QUAL/DOSINST/XRSYNC.JSN)
bind the helper, package, Setup selection, normal/cold launches and frame
hashes. The shared emulator lease and owned-process cleanup were used.
The existing RRTEST and RLE evidence retain their original scope.
