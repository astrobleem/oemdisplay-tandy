# OEMDisplay-Tandy
*Windows 3.0 real-mode display driver for the Tandy 1000 EX/HX*

---

## 📖 Overview
This project targets **Windows 3.0 real mode** on **8088-based Tandy 1000 EX/HX** computers using the **320×200, 16-color Tandy graphics mode**.

The current 8088 correction and reproducible build/test instructions are in [src/tandysw](src/tandysw/README.md). Emulator verification is documented separately from physical-hardware testing, which has not been performed. Windows 3.1 and standard/enhanced-mode compatibility are not claimed.

---

## Paintbrush showcase

![Tandy computer sketch drawn in Windows 3.0 Paintbrush](docs/tandy-8088-showcase.png)

A simplified sketch of the supplied Tandy photograph, drawn with native
Windows 3.0 Paintbrush tools on the tested 8088-compatible Tandy driver in
DOSBox-X. This unmodified native capture is 320×200 pixels in 16-color mode,
with normal 640 KB memory. The cyan lettering is part of the drawing.
This drawing capture predates the candidate05 bitmap-save correction; actual
colored BMP save/reopen is verified separately in the current tests.
Physical Tandy hardware has not been tested.

---

## ✨ Features
- Support for **320×200 16-color TGA mode**
- Correct palette handling and mode switching
- Targeted at **Windows 3.0 real mode** and the **8086/8088 instruction set**
- Normal 640KB shared-video-memory reservation helper, with fail-closed checks
- Built with **Microsoft C 6.0** and **MASM 5.1** using the official **Windows 3.x DDK**

## 🚧 Project Status
**MILESTONE 1 ACHIEVED (2025-12-02):** The driver `TNDY16.DRV` now builds and links successfully against the Windows 3.x DDK libraries!

The current correction is under active validation. Windows 3.0 has booted with the 8088-compatible build under an enforced 8086 instruction-set emulator, with live 320×200/16-color metrics and normal shared-memory reservation. See [current verification status](src/tandysw/STATUS88.TXT) for exactly which interaction checks have passed and which remain open.

---

## 🔧 Building
For the current 8088 correction, use Python 3 and DOSBox-X:

    python3 src/tandysw/BUILD88.PY --dosbox /path/to/dosbox-x --out /new/build

Follow [the current build, test and installation guide](src/tandysw/README.md).
The older `build_driver.bat` / `src/tandy16` path remains for historical development;
its separate instructions are in [BUILDING.md](BUILDING.MD).

---

## 🤝 Contributing
We welcome community contributions! If you encounter problems or have ideas for improvements, feel free to open an issue or submit a pull request.

## 📜 License
This project is released under the [GNU General Public License v3.0](LICENSE).
