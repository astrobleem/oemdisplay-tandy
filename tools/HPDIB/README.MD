# HPXY DIB optimization integration

This stage prepares the current PAN core with the general 4bpp DIB group
conversion improvement. It preserves the current PAN application, drivers,
fonts, grabber, support files, entry scripts, and consumer layout. The only
core payload changes are HPXY.DRV and the SETUP/FIXXT binaries whose exact
driver size/CRC pins must match it. Prior accepted packages remain immutable.

PREPARE.PY validates the accepted current PAN producer and the exact native
DIB build before compiling matching 8086 DOS installers with Open Watcom.
It produces a private expanded packet, ZIP and PREPARE.JSN. Its outcome is
PREPARED_NOT_QUALIFIED. It neither publishes nor establishes native acceptance.

BUILD.PY uses the pinned external HPXY source view and existing shared emulator
lease. Native builds and runs require an explicit coordinated slot, owned
watchdog, private fixtures and verified stop/release. No consumer Python,
manual INI edits, compiler/OS/ROM inputs, or nested archives enter the packet.

Independent review, repeated native DIB checks, actual FRESH/UPDATE/ordinary
Setup installation, installed PAN/application tests and final catalog checks
must pass before a publication proposal. Publication requires separate approval.
