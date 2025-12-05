# Handoff: Tandy 16-Color Display Driver Fixes

## Executive Summary
We are attempting to build the `TNDY16.DRV` display driver for Windows 3.0. The build process was failing with numerous linker errors (`L2029` Unresolved Externals). 

We have resolved the toolchain issues and several calling convention mismatches, reducing the error count significantly. The build now uses the correct linker (`LINK4`) and includes missing source files. However, 4-6 specific linker errors remain related to symbol visibility and export conflicts.

## Project Context
- **Working Directory**: `e:\BUILDATHING\oemdisplay-tandy\`
- **Source Directory**: `src\tandy16\`
- **Build Script**: `BLDTNDY.BAT` (run via `build_driver.bat` wrapper)
- **Def File**: `src\tandy16\tandy16.def` (and `TNDY16.DEF` in root)

## Completed Work

### 1. Toolchain Fix
- **Issue**: The build was using `LINK.EXE` v3.64 (OMF), which failed to process the `IMPORTS` section of the DEF file correctly, leading to unresolved Windows API symbols (`_GetModuleHandle`, etc.).
- **Fix**: Modified `BLDTNDY.BAT` to use `LINK4.EXE` (Segmented Executable Linker v5.x).

### 2. Import Resolution
- **Issue**: Windows API symbols were unresolved due to name decoration mismatches (C vs Pascal naming).
- **Fix**: Updated `src\tandy16\tandy16.def` and `TNDY16.DEF` to include **both** underscored (`_GetModuleHandle`) and non-underscored (`GetModuleHandle`) versions to satisfy all assembly modules regardless of their calling convention.

### 3. Calling Convention Standardization
- **Issue**: A mix of C (`?PLM=0`) and Pascal (`?PLM=1`) conventions caused internal linker errors. e.g., `CURSORS.ASM` was looking for `_draw_cursor` while `cursor.asm` exported `draw_cursor`.
- **Fix**: 
    - Forced `?PLM=1` (Pascal) in header of `CURSORS.ASM`, `cursor.asm`, and `FB.ASM`.
    - Added underscore aliases (e.g., `_hook_int_2Fh`) in `SSWITCH.ASM` to bridge remaining gaps.

### 4. Missing Source Files & Stubs
- **Issue**: `RealizeObject`, `Output`, `ColorInfo` were exported but undefined.
- **Fix**: 
    - Added `COLORINF.ASM` to `BLDTNDY.BAT` build list.
    - Created `stubs.asm` to provide no-op implementations for `RealizeObject` and `Output`.

## Current Status & Remaining Issues

The build runs but fails at the linker stage with the following output:

```
LINK : error L2023: Disable (alias Disable) : export imported
LINK : error L2022: DeviceMode (alias DeviceMode) : export undefined     
LINK : error L2023: Enable (alias Enable) : export imported
LINK : error L2022: ColorInfo (alias ColorInfo) : export undefined       
Unresolved externals:
_sum_RGB_colors_alt in file(s): COLORINF.OBJ(colorinf.asm)
COLOR_FORMAT in file(s): COLORINF.OBJ(colorinf.asm)
```

### Analysis of Remaining Errors

#### 1. `L2023: Disable/Enable : export imported`
- **Description**: The linker sees `Enable` and `Disable` being exported by our driver, but also sees them as being imported (likely from `LIBW.LIB` implicit import).
- **Theory**: `LIBW.LIB` contains these standard GDI functions. Our driver exports them to *be* the GDI.
- **Next Step**: Investigate linker flags (`/NOE` - No Extended Dictionary?) or check if `Enable` needs to be defined purely as `PUBLIC` without conflicting with the library. 

#### 2. `L2022: DeviceMode/ColorInfo : export undefined`
- **Description**: The DEF file exports these, but the linker can't find the definitions in the OBJ files.
- **Status**: 
    - `DeviceMode` IS defined in `SETMODE.ASM`.
    - `ColorInfo` IS defined in `COLORINF.ASM`.
- **Theory**: Possible `cProc` macro expansion issue or code segment discards. `SETMODE.ASM` uses `cBegin <nogen>`, which might be obscuring the public label if not handled right.
- **Next Step**: Check map file carefully for the exact symbol name generated for these functions (e.g. is it `DEVICECODE` all caps? Is it decorated?).

#### 3. Unresolved `_sum_RGB_colors_alt` & `COLOR_FORMAT`
- **Description**: referenced in `COLORINF.ASM`.
- **Next Step**: Find where these are defined. `COLOR.ASM` is a likely candidate. If missing, create stubs in `stubs.asm` or add the correct source file.

## Recommended Next Steps for Agent
1.  **Check `COLOR.ASM`**: Does it define `sum_RGB_colors_alt`? If not, stub it.
2.  **Investigate `L2022`**: Use `dumpbin` or `link /map` (already generated `tandy16.map`) to see exactly what symbols `SETMODE.OBJ` and `COLORINF.OBJ` are providing.
3.  **Fix `L2023`**: Try adding `/NOE` to the `link4` command in `BLDTNDY.BAT` to prevent `LIBW.LIB` from interfering with our exports.
