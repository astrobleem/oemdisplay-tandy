# Fresh CGA graphical Setup qualification

The exact native launcher and dedicated single-choice CGA640 OEM kit reach
original Windows 3.0 graphical Setup on an emulated IBM XT, 4.77 MHz 8088,
640 KB, RGBI CGA and DOS 6.22. Windows is absent at the start. No installed
driver is replaced as a substitute for a fresh test.

![Original graphical Windows Setup with project CGA640](SETUP.PNG)

`NATIVE.JSN` binds the final archives, original-media identities, selected
boot entries, installed support, refusals and cleanup. `EXACTRUN.JSN` retains
the controller actions. `BUILD.JSN` and `HOST.JSN` pin the build and an
identical standalone-source rebuild. `RUNTIME.JSN` documents the final
archive's instruction/notice changes after native staging; all twelve runtime files
are identical. The original four floppy images were copied unchanged into
one private media-source directory; a full floppy-swapping sequence was not
exercised. Original Setup copied/decompressed the OS in the emulated 8088.

`FIRST.JSN`, `FIRST-RUN.JSN` and `FIRST.PNG` retain the earlier architecture
test using the accepted CGA packet directly on PC-DOS 3.20. That is separate
from the new launcher's DOS 3.3+ test. `PREFLIGHT.JSN` retains the failed
missing-path launch attempt, which started no emulator. The private harness
sources are retained developer evidence and reference external owned OS
fixtures/dependencies. They are not consumer preparation tools.

**Scope:** entry into the original graphical Setup options dialog. Complete
OS installation, a first ordinary WIN /R start, other fresh profiles, and
physical hardware remain untested. Existing installed-driver qualifications
are not inherited as fresh-install results. No publication is authorized.
Both owned emulators stopped, the shared byte lease was released and checked
available afterward, and emulator inventory ended at zero. No playback or
runner is queued. Disk images, OS files, compiler and emulator are excluded.
