# OEMDisplay-Tandy  
*Windows 3.x OEM Display Driver for the Tandy 1000 Series*  

![Tandy 1000 Logo](docs/images/tandy-logo.png)  
![Windows 3.x Logo](docs/images/win3x-logo.png)  

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

---

## 🖥️ Requirements  
- Tandy 1000 series system (EX, HX, TX, RL, or compatible)  
- MS-DOS 3.2+  
- Windows 3.0 or 3.1 (Real or Standard Mode)  
- Development system (for building):  
  - 386 or better  
  - Microsoft C 6.0  
  - Microsoft Macro Assembler 5.1  
  - Windows 3.x DDK  

---

## 🔧 Building  
1. Install Microsoft C 6.0 and MASM 5.1 on your development VM (DOS 6.22 + Windows 3.1 recommended).  
2. Clone this repository or transfer the source to your VM.  
3. From the DOS prompt, run:  
   ```sh
   nmake tandy16.mak
