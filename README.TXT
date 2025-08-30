OEMDisplay-Tandy
Windows 3.x OEM display driver for the Tandy 1000 series

Overview
--------
This driver enables the Tandy Graphics Adapter (TGA) 320x200 16-color mode
under Windows 3.0 and 3.1.

Features
--------
- 320x200 16-color TGA support
- Correct palette handling and mode switching
- Works with Windows 3.0 and 3.1 (Real or Standard Mode)

Requirements
------------
- Tandy 1000 series computer
- MS-DOS 3.2 or later
- Windows 3.0 or 3.1
- Microsoft C 6.0 and MASM 5.1 with the Windows 3.x DDK (for building)

Building
--------
1. Install Microsoft C 6.0 and MASM 5.1.
2. From the DOS prompt, run:
   NMAKE TANDY16.MAK

License
-------
This project is released under the MIT License. See LICENSE for details.
