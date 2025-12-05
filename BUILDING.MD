
# BUILDING

This project targets 16-bit Windows using Microsoft C 6.0.

## Prerequisites

- DOSBox-X
- MS-DOS with Microsoft C 6.0 installed under `BIN`, `LIB` and `INCLUDE`.
- `PKZIP.EXE` and `UNIX2DOS.EXE` available on the DOS `PATH`.

## Building

For a clean build using the automated script:

```cmd
build_driver.bat
```

This script:
1.  Starts DOSBox-X.
2.  Mounts the repository.
3.  Runs the 5-stage build process (`BLDTNDY.BAT`).
4.  Checks for the output file `TNDY16.DRV`.

**Manual Build (inside DOSBox-X):**
1.  `MOUNT C <repo>`
2.  `C:`
3.  `BLDTNDY.BAT` (or `BLDTNDY.BAT <stage>` to resume)

The build produces `TNDY16.DRV` in the root directory.


## Testing

1. Copy the resulting `TNDY16.DRV` into a Windows 3.x installation.
2. Select the driver through Windows Setup and confirm that the display initializes correctly.


