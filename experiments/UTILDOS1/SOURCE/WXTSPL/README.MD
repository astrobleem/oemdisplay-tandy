# Building the UTILDOS1 WXTSPL trial

Use your licensed Microsoft C6 compiler, C runtime and segmented LINK4.
The tested build uses /G0 /AS /W3 /Od and an 8192-byte stack, linking SLIBCE.
The kit-level QA/DOSBUILD.PY reproduces the exact tested commands in a new
output directory. The native SHA-256 self-test must pass before using output.

Qualified executable SHA-256:
0a876e4620b4dd426ffeac7912b2023a08e80d271320295cb52086b431b74e5b
Two native builds matched. The new CHECK text changes no accepted hashes,
transaction functions, DOS guards, path limits or interruption checkpoints.

For POSIX host tests:
cc -x c -DHOST_TEST -D_POSIX_C_SOURCE=200809L -DS_IREAD=S_IRUSR
 -DS_IWRITE=S_IWUSR -std=c89 -O1 -g -fsanitize=address,undefined
 -o wxtspl-host SPLASH.C
ASAN_OPTIONS=detect_leaks=0 python3 TEST.PY --exe ./wxtspl-host
 --stock-win-com OWNED_WIN_COM --old-tandy-rle OWNED_REPO/src/splash/assets/TNDYLOGO.RLE

Join wrapped commands onto one line. The test reads your recognized original
and first-party artwork, then operates exclusively on temporary copies.
Its 1,048 cases include named-state/next-command output assertions, unknown
files, directories, symlinks, idempotence and corruption. This does not prove
physical FAT/media behavior. No owned Windows loader bytes are included.
