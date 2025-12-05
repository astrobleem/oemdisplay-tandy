
# BUILDING

This project targets 16-bit Windows 3.0 using MASM 5.10.

## Prerequisites

- **Host:** Windows 10/11 with PowerShell.
- **Emulator:** DOSBox-X (included in `DOSBox-X/`).
- **Tools:** `MASM 5.10` and `LINK4.EXE` (included in `BIN/`).

## Building

### Automated Build (Recommended)
From the host command prompt:

```cmd
build_driver.bat
```

This script:
1.  Starts DOSBox-X.
2.  Runs the 5-stage build process (`BLDTNDY.BAT`) inside the emulator.
3.  Checks for the output file `TNDY16.DRV`.

### Packaging (Release)
To create a distribution zip (`TNDY16.ZIP`):

```cmd
makedisk.bat
```

This script:
1.  Builds the driver if missing.
2.  Creates a `TNDY16` folder with the driver and INF files.
3.  Converts text files to DOS format.
4.  Zips contents into `TNDY16.ZIP`.

## Manual Build (Debugging)
Inside DOSBox-X:
1.  `MOUNT C <repo>` (Auto-mounted by `dosbox-x.conf`)
2.  `C:`
3.  `BLDTNDY.BAT` (or `BLDTNDY.BAT <stage>` to resume)

## Testing

1. Copy the resulting `TNDY16.DRV` (or unzip `TNDY16.ZIP`) into a Windows 3.0 installation.
2. Select the driver through Windows Setup and confirm that the display initializes correctly.


