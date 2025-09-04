# Tandy 1000 Windows 3.x Display Driver

This is a 16-bit Windows 3.x display driver for the Tandy Graphics Adapter (TGA) 320×200 16-color mode. The driver enables proper use of Tandy 1000 series graphics capabilities under Windows 3.0/3.1.

**ALWAYS reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.**

## Critical Build Constraints

**DO NOT attempt to build this project in a modern Linux environment.** This project:
- Requires Microsoft C 6.0 or 7.0 targeting 16-bit real-mode
- Must be built inside DOSBox or PCem with MS-DOS and Windows 3.x
- Uses 16-bit MASM 5.1 for assembly language components
- Targets Windows 3.x compatibility; strictly C89 only

## Working Effectively

### Environment Setup Requirements
- Install DOSBox or PCem emulator
- Install MS-DOS 6.22 or compatible in the emulator  
- Install Microsoft C 6.0 or 7.0 compiler toolchain
- Install Microsoft Macro Assembler (MASM) 5.1
- Install Windows 3.x DDK (Device Driver Kit)
- Mount this repository as a drive in the emulator
- Set PATH to include the Microsoft C and MASM tools

### Build Process (Inside DOSBox/PCem)
The build process consists of two phases:

**Phase 1 - Compile and Assemble (5-10 minutes):**
```batch
nmake tndy16.mak
```
This command:
- Compiles `src/dllentry.c` → `dllentry.obj`
- Compiles `src/enable.c` → `enable.obj` 
- Assembles `src/tgavid.asm` → `tgavid.obj`

**Phase 2 - Link Driver (2-5 minutes):**
```batch
mkdrv.bat
```
This command links the object files to create `tndy16.drv` using Windows 3.x libraries.

**Alternative Build (Complete Process):**
```batch
BUILD.BAT
```
This runs `nmake tndy16.mak > build.log` and logs output.

**NEVER CANCEL these build commands.** The build process typically takes 10-15 minutes total. Set timeout to 30+ minutes.

### Build Outputs
Successful build produces:
- `dllentry.obj` - DLL entry point object
- `enable.obj` - Main driver logic object  
- `tgavid.obj` - Assembly hardware interface object
- `tndy16.drv` - Final Windows 3.x driver binary

## Validation

### Build Validation
After building, verify these files exist:
- All `.obj` files in project root
- `tndy16.drv` driver binary
- `build.log` (if using BUILD.BAT)

### Manual Testing Requirements
**You MUST manually test the driver on Windows 3.x:**
1. Copy `tndy16.drv` to Windows 3.x SYSTEM directory
2. Run Windows Setup to install the driver using `oemsetup.inf`
3. Restart Windows and verify the driver loads without errors
4. Test basic graphics operations (drawing, colors, palette)
5. Verify the 320×200 16-color mode works correctly

**This project has NO automated testing.** All validation must be done manually on actual Windows 3.x systems or emulation.

## Coding Standards

### Strict Requirements
- **C89 only** - No C99 or C++ features allowed
- **4-space indentation** - Tabs are forbidden  
- **80 column limit** - Keep all lines ≤ 80 characters
- **Explicit types** - Use `uint8_t`, `UINT16`, etc.
- **Void parameters** - Functions with no params must declare `void`
- **16-bit targeting** - All code must work in 16-bit real mode

### Example Formatting
```c
int FAR PASCAL Enable(LPDEVICE lpDevice)
{
    if (!TGA_Detect()) {
        return 0;
    }
    /* 4-space indent, explicit void, 80 cols max */
    return 1;
}
```

## Common Tasks

### Repository Structure
```
/home/runner/work/oemdisplay-tandy/oemdisplay-tandy/
├── BUILD.BAT           # Main build script
├── tndy16.mak         # NMAKE makefile  
├── mkdrv.bat          # Driver linking script
├── TNDY16.DEF         # Module definition file
├── oemsetup.inf       # Windows Setup information
├── src/               # Source code directory
│   ├── dllentry.c     # DLL entry points
│   ├── enable.c       # Main driver logic
│   ├── tgavid.asm     # Hardware interface (assembly)
│   ├── tndy16.h       # Driver header
│   ├── TGAVID.H       # Hardware interface header
│   ├── COMPAT.H       # Compiler compatibility  
│   ├── windows.h      # Windows 3.x API definitions
│   └── *.h            # Various header files
├── README.md          # Project documentation
├── AGENTS.md          # Build environment constraints
└── LICENSE            # GPL v3.0 license
```

### Key Source Files
- **`src/enable.c`** - Main driver initialization and GDI interface (150 lines)
- **`src/tgavid.asm`** - Low-level TGA hardware control (MASM, ~100 lines)
- **`src/dllentry.c`** - Windows DLL entry/exit points (23 lines)
- **`TNDY16.DEF`** - Exports Enable, Disable, DeviceMode, ColorInfo

### Driver Exports (from TNDY16.DEF)
```
LIBRARY TNDY16.DRV
DESCRIPTION 'Tandy 16-color driver'
EXPORTS
        Enable
        Disable  
        DeviceMode
        ColorInfo
```

### Common Editing Tasks
When modifying the driver:
- **Hardware detection**: Edit `TGA_Detect()` in `src/tgavid.asm`
- **Mode setting**: Modify `TGA_SetMode()` in `src/tgavid.asm`
- **GDI interface**: Update `Enable()` function in `src/enable.c`
- **Color support**: Edit palette handling in `enable.c`
- **Memory management**: Modify shadow buffer allocation in `enable.c`

### Build Dependencies
The makefile defines these dependencies:
- `dllentry.obj` ← `src/dllentry.c`
- `enable.obj` ← `src/enable.c`, `src/tndy16.h`  
- `tgavid.obj` ← `src/tgavid.asm`

### Development Workflow
1. Make changes to source files using C89 standards
2. Build in DOSBox/PCem: `nmake tndy16.mak && mkdrv.bat`
3. Test on Windows 3.x (Real or Standard Mode)
4. Verify driver loads and graphics work correctly
5. Document any issues or hardware compatibility notes

### Build Command Details
The exact makefile targets and compiler flags are:
```makefile
CC = cl
ML = masm
CFLAGS = /c /W3
MASMFLAGS = -v -ML -I.\
```

Clean build artifacts with:
```batch
nmake tndy16.mak clean
```

### File Size Expectations
After successful build:
- Object files: ~2-8KB each
- Final driver: ~15-25KB (tndy16.drv)

## Limitations

### What DOES NOT Work
- **Modern toolchains** - GCC, Clang, Visual Studio cannot build this
- **Linux/macOS native** - Project requires DOS/Windows 3.x environment
- **64-bit targets** - Driver is strictly 16-bit real mode only
- **Automated CI/CD** - No GitHub Actions or modern CI possible
- **Unit testing** - No test framework; manual validation only

### Environment Constraints  
- **Emulation required** - Must use DOSBox or PCem
- **Legacy toolchain** - Microsoft C 6.0/7.0 and MASM 5.1 only
- **Manual builds** - No cross-compilation from modern systems
- **Manual testing** - Requires Windows 3.x installation to validate

## Troubleshooting

### Build Failures
- Ensure Microsoft C 6.0/7.0 is in PATH
- Verify MASM 5.1 is installed and accessible
- Check that Windows 3.x DDK libraries are available
- Confirm all source files use CRLF line endings (DOS format)

### Driver Issues
- Test driver installation using Windows Setup
- Check Windows 3.x System directory for `tndy16.drv`
- Verify hardware detection logic in `TGA_Detect()`
- Test on actual Tandy 1000 hardware if emulation fails

## Pull Request Requirements

When submitting changes:
1. Explain the DOSBox/PCem environment setup used
2. Include build logs showing successful compilation
3. Provide screenshots of Windows 3.x with driver loaded
4. Document any hardware compatibility testing performed
5. Keep commits focused and reference relevant issues
6. Ensure all code follows the C89 and formatting standards

**Remember: This is legacy 16-bit development requiring period-appropriate tools and extensive manual validation.**

## Quick Reference

### Essential Commands (DOSBox/PCem only)
```batch
nmake tndy16.mak          # Compile all source files
mkdrv.bat                 # Link driver
BUILD.BAT                 # Complete build with logging
nmake tndy16.mak clean    # Remove object files
```

### Files Modified Most Often
1. `src/enable.c` - Driver logic and Windows GDI interface
2. `src/tgavid.asm` - Hardware-specific assembly code
3. `oemsetup.inf` - Windows installation configuration
4. `TNDY16.DEF` - DLL export definitions

### Critical File Sizes
- Source files: 500-5000 bytes each
- Object files: 2-8KB each  
- Final driver: 15-25KB (tndy16.drv)
- Build log: Varies (build.log)

### Error Patterns
- "Bad command or file name" → Missing Microsoft C/MASM in PATH
- "Cannot open include file" → Missing Windows 3.x DDK headers
- "Unresolved externals" → Missing Windows 3.x libraries during link
- "Invalid object module" → Mixed 16-bit/32-bit object files