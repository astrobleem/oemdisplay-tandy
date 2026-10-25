# Native consumer installers

WINXTDOS.ZIP contains the ready-to-run WINXT.EXE and a short README.
The separate WINXT.ZIP is the raw preparer kit.
The publisher checks extracted WINXT.EXE bytes against the qualified EXE.

The prebuilt XRSYNC.EXE and WINXT.EXE run on the DOS computer itself. Both
include the supplied, expanded CGA.GR2 grabber and all driver support files;
consumers do not collect support files or run Python. The FullXT finisher
installs the canonical SOUND.DRV shared by the desktop alerts and Tandy
Winamp, together with their current shell and sound clients.

XRSYNC installs the display into an existing Windows 3.0 system:

```bat
XRSYNC C:\WINDOWS
```

WINXT prepares the complete current desktop, using the installed Windows OS
or gathering the original Windows 3.0 Setup disks automatically:

```bat
WINXT UPDATE C:\WINDOWS
WINXT FRESH A:\
```

XRSYNC targets DOS 3.20+; WINXT targets DOS 3.3+. Both target the 8088 and
normal 640 KB. The Windows/DOS installation, private prepared OS files,
toolchain, emulator and guest disk images are outside the public packets.

Developer rebuilds use Open Watcom's 16-bit DOS compiler:

```text
python tools/DOSINST/BUILD.PY --watcom C:\WATCOM --target xrsync --out NEWBUILD
python tools/DOSINST/BUILD.PY --watcom C:\WATCOM --target rc8 --out NEWBUILD
python tools/DOSINST/BUILD.PY --watcom C:\WATCOM --target finisher --out NEWBUILD
python tools/DOSINST/BUILD.PY --watcom C:\WATCOM --target wrapper --out NEWBUILD
```

Use a fresh output directory for each command. XSNATIVE.JSN and RCNATIVE.JSN
bind the source and prebuilt binary identities. The public publishers refuse
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
The corresponding sound source and existing license accompany the native
packet in `SOUNDSRC.ZIP` and `SOUNDLIC.TXT`.
