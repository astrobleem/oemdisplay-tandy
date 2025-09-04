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
