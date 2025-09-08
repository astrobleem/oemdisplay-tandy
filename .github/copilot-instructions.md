# GitHub Copilot Instructions for OEMDisplay-Tandy

This repository contains a Windows 3.x display driver for Tandy 1000 series computers. When working on this project, please follow these specific guidelines derived from our development practices.

## Environment Setup Requirements

**CRITICAL: This project requires a very specific vintage development environment**

- Install prerequisites up front: `sudo apt-get install -y dosbox-x unix2dos file dos2unix`
- All development and building MUST occur inside DOSBox-X - Linux shell builds are unsupported
- Mount this repository in DOSBox-X and set DOS toolchain paths:
  - Set PATH, LIB, and INCLUDE variables to point at bundled MS C 6.0 directories
- Use a DOS 6.22 + Windows 3.1 development VM when possible

## Critical Build Constraints

- **Compiler**: Microsoft C 6.0 or 7.0 only - targeting 16-bit real-mode
- **Compatibility**: Windows 3.x compatibility required - avoid features past C89
- **Architecture**: 16-bit real-mode DOS executable format
- **Build Tool**: Use provided BUILD.BAT from project root inside DOSBox-X emulator

## Coding Style Requirements

**Language**: Strictly C89 - NO C99 or C++ features allowed

**Formatting**:
- Indent with four spaces - tabs are forbidden
- Keep lines at 80 columns or fewer
- Functions with no parameters must declare `void`
- Use explicit-width integers (e.g. `uint8_t`, `UINT16`)

**File Handling**:
- Maintain DOS-friendly files with CRLF line endings using `unix2dos`
- Keep filenames in 8.3 uppercase form
- Delete .EXE, .OBJ, or .TXT artifacts before committing

## Build & Test Process

1. **Clean Build**: From DOSBox-X session, delete old binaries first
2. **Build Command**: Run `build` (BUILD.BAT) from project root
3. **Validation**: Batch file must complete without errors and emit driver binaries
4. **Testing**: Verify driver loads on clean Windows 3.x setup
5. **No CI**: Manual builds in DOSBox or PCem are mandatory - no automated CI exists

## Development Workflow

**Prerequisites Check**: Always verify DOSBox-X and line-ending utilities are installed
**Environment**: Work exclusively inside DOSBox-X - never attempt Linux shell builds
**Testing**: Run clean build and test from DOSBox-X session to verify expected output

## Pull Request Expectations

- Explain environment and steps taken to build and test
- Include logs or screenshots proving `build` succeeded
- Keep commits focused and reference relevant issues when available
- Demonstrate testing on actual Windows 3.x setup when possible

## Key Reminders for AI Assistants

- This is NOT a modern project - vintage development constraints apply
- 16-bit real-mode programming has different constraints than modern development
- DOSBox-X emulation is required for authentic build environment
- Manual testing procedures replace automated CI/CD
- File format compatibility (DOS 8.3, CRLF) is critical for functionality