# Tandy 16-Color Driver Build Tasks

- [x] **Phase 1: Toolchain & Fixes**
    - [x] Switch build to use `LINK4.EXE` (Segmented Exe Linker) to support Windows 3.0 DEF import syntax.
    - [x] Fix `BLDTNDY.BAT` to invoke `LINK4`.
    - [x] Update `TNDY16.DEF` and `tandy16.def` to include underscored imports for `KERNEL` and `KEYBOARD` symbols.
    - [x] Standardize calling conventions to Pascal (`?PLM=1`) in `cursor.asm`, `FB.ASM`, and `CURSORS.ASM` to match `ENABLE.ASM`.
    - [x] Add underscore aliases in `SSWITCH.ASM` (`_hook_int_2Fh`, etc.) for compatibility.
    - [x] Create `stubs.asm` for missing `RealizeObject` and `Output` exports.
    - [x] Add `COLORINF.ASM` to the build list.

- [/] **Phase 2: Resolving Remaining Linker Errors**
    - [ ] Resolve `L2023: export imported` for `Enable` and `Disable`.
        - *Investigation*: Likely conflict between explicitly exported functions and `LIBW.LIB` implicit imports.
    - [ ] Resolve `L2022: export undefined` for `DeviceMode` and `ColorInfo`.
        - *Investigation*: verify `cProc` expansion and public visibility in `SETMODE.ASM` and `COLORINF.ASM`.
    - [ ] Link missing internal symbol `_sum_RGB_colors_alt`.
        - *Investigation*: Check `COLOR.ASM` for definition or provide stub.
    - [ ] Link missing data symbol `COLOR_FORMAT`.
    - [ ] Fix Intersegment fixup warning for `TGA_SetMode`.

- [ ] **Phase 3: Verification**
    - [ ] Successfully link `TNDY16.DRV` without errors.
    - [ ] Verify driver loads in Windows environment (if possible).
