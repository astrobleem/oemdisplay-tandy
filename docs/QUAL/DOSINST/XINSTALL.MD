# Native XRSYNC installer correction

The consumer packet includes the supplied `CGA.GR2`. Its repository source is
1,768-byte SZDD mode A; bounded expansion produces the same qualified 2,104-byte
grabber (`1fc24254a1b76c2030a0ae60e25a17d6df4730c2a99d293ca22886059d8be067`).
No Windows support file is collected from the user. Installed Windows 3.0
provides the OS and its normal Setup program.

The space preflight counts cluster-rounded missing payloads, the retained
checker, generated launcher, directory entries and 128 KiB of Setup headroom.
The installed checker keeps only the executable image; the download's archive
overlay is unnecessary for `/CHECK`. New writes use create-new files, close and
readback before commit. Failure removes the current incomplete output. Rerun
reuses verified completed payloads and replaces an incomplete named checker.

`XSPACE.JSN` binds the native recovery test, logs, selected Setup screen and
exact packet. On DOS 3.20 / 8088 / 640 KB with 2,048-byte clusters and 262,144
bytes free, the old installer accepted 237,568 bytes as sufficient and left a
155,648-byte truncated helper on a full disk. The correction required 288,768
bytes and stopped before staging. After freeing the owned fixture filler,
repair succeeded with the installed-Windows grabber absent. Injected helper
write failure removed its temporary file; the next retry succeeded. Normal
Windows Setup then selected the supplied driver/fonts/grabber and the probe
completed. All 17 frame hashes match the qualified rendering reference.

The reusable guest batch is `XSPCTST.BAT`; it is a test sequence for an isolated
fixture, excluded from the consumer packet. `NEW.EXE` is the recorded packet,
`OLD.EXE` is built from the recorded old source commit, and `FAULT.EXE` uses the
recorded failure macro. DOS/Windows images and proprietary tools are excluded.

Rendering executables are unchanged. This records emulator installation and
recovery qualification; it makes no physical-hardware claim.
