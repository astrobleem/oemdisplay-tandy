Install prerequisites up front. Run sudo apt-get install -y dosbox-x file dos2unix so the DOSBox emulator and line-ending utilities are ready before any edits

Work inside DOSBox-X. Mount the repository in DOSBox-X and run the build script there; building from the Linux shell is unsupported

Set DOS toolchain paths. Within DOSBox-X, set PATH, LIB, and INCLUDE variables to point at the bundled MS C 6.0 directories before compiling

Maintain DOS-friendly files. Use unix2dos to preserve CRLF line endings, keep filenames in 8.3 uppercase form, and delete any .EXE, .OBJ, or .TXT artifacts before committing

Run a clean build and test. From a DOSBox-X session, delete old binaries, invoke build, then install the driver in Windows 3.x to confirm it loads

# Critical build constraints
- Build with Microsoft C 6.0 or 7.0 targeting 16-bit real-mode.
- Assume Windows 3.x compatibility; avoid features past C89.

# Environment setup
- Develop inside DOSBox or PCem.
- Install MS-DOS and the Microsoft C toolchain in the emulator.
- Share this repository as a drive and set PATH for the compiler tools.

# Coding style
- Strictly C89; no C99 or C++ features.
- Indent with four spaces; tabs are forbidden.
- Keep lines at 80 columns or fewer.
- Use explicit-width integers (e.g. `uint8_t`, `UINT16`).
- Functions with no parameters must declare `void`.

# Build & test
- Run `build` (BUILD.BAT) from the project root inside the emulator.
- The batch file must complete without errors and emit driver binaries.
- Verify the driver loads on a clean Windows 3.x setup.

# CI
- No automated CI exists; manual builds in DOSBox or PCem are mandatory.

# Pull request expectations
- Explain environment and steps taken to build and test.
- Include logs or screenshots proving `build` succeeded.
- Keep commits focused and reference relevant issues when available.
