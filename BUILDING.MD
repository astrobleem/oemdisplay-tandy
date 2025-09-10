
# BUILDING

This project targets 16-bit Windows using Microsoft C 6.0.

## Prerequisites

- DOSBox-X
- MS-DOS with Microsoft C 6.0 installed under `BIN`, `LIB` and `INCLUDE`.
- Info-ZIP `ZIP.EXE` and `UNIX2DOS.EXE` available on the DOS `PATH`.

## Building and Packaging

For a clean build run:

```
dosbox-x -no-console -conf dosbox-x.conf
```

The configuration mounts this repository, clears previous binaries, and
executes `BUILD.BAT` with output redirected to `OUT.TXT`. Review
`OUT.TXT` to confirm the build succeeded.

1. Start DOSBox-X.
2. Mount the repository as drive C: `MOUNT C <repo>`.
3. Set the toolchain environment:
   ``SET PATH=C:\BIN;%PATH%``
   ``SET LIB=C:\LIB``
   ``SET INCLUDE=C:\INCLUDE``
4. Run `MAKEDISK` to build the driver and create `TNDY16.ZIP`.
5. The ZIP contains `TNDY16.DRV`, `OEMSETUP.INF`,
   `FILE_ID.DIZ` and `README.TXT` ready for distribution.


## Testing

1. Copy the resulting `TNDY16.DRV` into a Windows 3.x installation.
2. Select the driver through Windows Setup and confirm that the display initializes correctly.

