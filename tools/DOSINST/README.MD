# Native consumer installers

The current WINXT.ZIP extracts SETUP.EXE, README.TXT and one WINXT folder
of actual expanded files. The native SETUP reads that adjacent folder; it
neither opens an archive nor requires the original ZIP after extraction.

Run SETUP UPDATE C:\WINDOWS for the full desktop using an installed OS, or
SETUP FRESH A:\ to gather the original Windows 3.0 disks automatically.
The same expanded folder is an ordinary Windows Setup source for drivers
only. Its guarded DISPLAY and DISPWIN entries are documented inside it.
Full desktop preparation requires DOS 3.3+; the driver-only route targets
DOS 3.20+. Both target 8088/640 KB Windows 3.0 real mode.

Runtime files, the supplied grabber, own fonts/logos and component licences
are included. Windows/DOS OS files, private prepared trees, compiler and
emulator remain outside publication. Current SOUND corresponding source is
the separate WINXTSRC.ZIP developer asset alongside the download.

Developer SETUP, preparer and wrapper builds use Open Watcom's 16-bit DOS tools:

```text
python tools/DOSINST/BUILD.PY --watcom C:\WATCOM --target xrsync --out NEW-XRSYNC
python tools/DOSINST/BUILD.PY --watcom C:\WATCOM --target setup --out NEW-SETUP
python tools/DOSINST/BUILD.PY --watcom C:\WATCOM --target wrapper --out NEW-WRAPPER
```

Use a different fresh output directory for each command. SETNAT.JSN binds the
current expanded SETUP source/binary; XSNATIVE.JSN and RCNATIVE.JSN preserve
the earlier native preparer bindings. The public publishers refuse
assets that differ from their native qualification records. Developer-only
Python reference recipes remain outside consumer downloads.
XRINPUT.H pins the CRC of every required expanded Windows OS stream;
XRINPUT.JSN binds those CRCs to the existing qualified size/SHA identities.
The helper checks CRC during its existing reads and withholds the new Setup
entry on failure. It discards a rejected copy only in its own tagged media
cache, so a normal retry gathers that file again from the original media.

[Display installation results](../../docs/QUAL/DOSINST/XRSYNC.JSN) and
[complete desktop installation results](../../docs/QUAL/DOSINST/RC8.JSN)
record the native preparation, Setup and guarded launch checks. Rendering
qualification remains separate from installation qualification.

The canonical finisher source is `tools/DOSINST/FIXXT.C`; its generated
`SOUNDID.H` is byte-identical to the canonical OEMSound driver's header.
The checked C6 finisher build route is `tools/SOUNDOWN/FINBUILD.PY`, with
explicit external toolchain, installed DOSBox-X and shared lease arguments.
The accepted C6 route is:

```text
python tools/SOUNDOWN/FINBUILD.PY --toolchain C6-TOOLCHAIN --dosbox DOSBOX-X --lease SHARED-LEASE --out NEW-FIXXT
```

This starts a bounded leased native build. `BUILD.PY --target finisher` uses
Open Watcom and does not reproduce the accepted C6 FIXXT binary in FIXBUILD.JSN.
The corresponding sound source is the separate current `WINXTSRC.ZIP`
developer asset; `SOUNDLIC.TXT` is included in the expanded WINXT folder.
