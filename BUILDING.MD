
# BUILDING

This project targets 16-bit Windows using Microsoft C 6.0.

## Prerequisites

- DOSBox-X
- MS-DOS with Microsoft C 6.0 installed under `BIN`, `LIB` and `INCLUDE`.
- `PKZIP.EXE` and `UNIX2DOS.EXE` available on the DOS `PATH`.

## Building and Packaging

For a clean build that records log output:

```
dosbox-x -conf dosbox-x.conf -c "BUILD.BAT > OUT.TXT" -c "EXIT"
```

This mounts the repository, sets the toolchain environment, runs
`BUILD.BAT` once, and leaves `OUT.TXT` and `BUILD.LOG` in the repository
for review.

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


