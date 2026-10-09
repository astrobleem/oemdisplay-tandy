# Install Windows XT rc.5

Download WINXT720.IMG or WINXT720.ZIP from the rc.5 release. This is a 720 KB
data disk for existing DOS 3.3+ and Windows 3.0 real mode, not a boot/OS disk.
At the floppy root run INSTALL, optionally giving an owned support folder.
Confirm the fresh C:\WINXT stage. Then C: / CD \WINXT / INSTALL. Run
C:\WINXT\WINXT SETUP, choose Other display, use C:\WINXT at every source
prompt and Complete Changes. Start using C:\WINXT\WINXT. Rollback after
Windows exits using the numbered BACKUP\B001\RESTORE YES path printed
by INSTALL. Existing video/recovery guards remain mandatory.

Seven original MIT fonts are included. No Windows font setup media, private
font transplant or Python is needed on the Tandy. Only CGA.GR2 (2104 bytes)
and CGALOGO.LGO (880 bytes) are gathered from owned non-font support files.
Windows itself and other existing non-font dependencies remain required.
Expanded or compressed owned inputs are supported; malformed sizes/streams,
missing inputs, existing output and insufficient space are refused.

Normal preparation/install/start performs zero SHA verification work. /VERIFY
is optional, expensive developer diagnostics. The qualified faster guarded
startup and original backup behavior are retained. Setup owns display/font
installation. At 160 pixels wide dialogs can clip; text mode is experimental.
See the [manual](../../docs/USERMAN.MD) and [font guide](../../docs/FONTS/README.MD).

The rebuilt PREPXT/TINST and exact image passed default and /VERIFY native
transactions and rollback. Current QUALIFY.JSON certifies the unchanged
pre-native BUILD/README snapshots in the download. Modern host reproduction
uses TESTFAT.PY, TESTPKG.PY and MAKEIMG.PY; original-font generation and the
publication gate are in ../XTFONTS. No emulator is used by public package CI.
