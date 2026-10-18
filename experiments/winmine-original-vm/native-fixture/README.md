# Native Win16 API fixture

This first-party MSC6 fixture checks the real Win16 `GetVersion` and
`EnumWindows` APIs. Its exported `BOOL FAR PASCAL` callback is passed through
`MakeProcInstance`, then invoked by Windows during enumeration. The log records
the version value, callback HWND/LPARAM pairs, full-enumeration return, and the
early-stop return after a callback returns `FALSE`. After closing the log, the
one-shot fixture requests Windows exit so the guest can return to DOS.

`BUILD.BAT` builds the private `W16APIN.EXE` with Microsoft C 6.0 and LINK4,
with the toolchain mounted as `C:` and this directory mounted as `S:`. A
machine-specific `BUILD.CNF` can supply those mounts in DOSBox-X; it is not
included because its host paths are local. The runtime fixture writes
`C:\W16API.LOG` on the guest. Do not commit or publish the executable or guest
image.

The Windows 3.0/8088 guest run is a compatibility check for this API path; it
does not qualify an OEM display driver or Minesweeper runtime. Record emulator,
machine profile, guest version, tested source commit, and log when reporting a
run. Emulator results must not be described as physical-hardware qualification.

Current validation: MSC6 and LINK4 produced a Windows NE executable
(`BUILD=PASS`). Native Windows 3.0 execution has not yet been completed, so no
guest API result is claimed.
