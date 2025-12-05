# OEMDisplay-Tandy
*Windows 3.x OEM Display Driver for the Tandy 1000 Series*

---

## 📖 Overview
This project provides a **Windows 3.x display driver** for the **Tandy 1000 series** of computers, enabling proper use of the **Tandy Graphics Adapter (TGA)** 320×200 16-color mode.

By default, Windows 3.0/3.1 only offers **CGA (2 colors)** or **EGA (limited support)** on Tandy hardware. This driver restores the full visual potential of the platform, giving your Tandy 1000 a native Windows 3.x experience.

---

## ✨ Features
- Support for **320×200 16-color TGA mode**
- Correct palette handling and mode switching
- Compatible with **Windows 3.0** and **Windows 3.1** (Standard & Real Mode)
- Built with **Microsoft C 6.0** and **MASM 5.1** using the official **Windows 3.x DDK**

## 🚧 Project Status
**MILESTONE 1 ACHIEVED (2025-12-02):** The driver `TNDY16.DRV` now builds and links successfully against the Windows 3.x DDK libraries!

This driver is under active development. The next phase involves verifying functionality in a live Windows 3.0 environment.

---

## 🔧 Building
1.  Ensure **DOSBox-X** is installed and available.
2.  Run the automated build script from the project root:
    ```cmd
    build_driver.bat
    ```
3.  For detailed instructions, see [BUILDING.md](BUILDING.MD).

---

## 🤝 Contributing
We welcome community contributions! If you encounter problems or have ideas for improvements, feel free to open an issue or submit a pull request.

## 📜 License
This project is released under the [GNU General Public License v3.0](LICENSE).
