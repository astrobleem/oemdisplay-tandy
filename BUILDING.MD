# Building OEMDisplay-Tandy

## Building

1. Mount this repository as drive `C:` inside DOSBox-X.
2. Configure the Microsoft C 6.0 environment:
   ```
   SET PATH=C:\BIN;%PATH%
   SET LIB=C:\LIB
   SET INCLUDE=C:\INCLUDE
   ```
3. Run `BUILD` to compile the driver.

## Testing

1. Copy the resulting `TNDY16.DRV` into a Windows 3.x installation.
2. Select the driver through Windows Setup and confirm that the display initializes correctly.
