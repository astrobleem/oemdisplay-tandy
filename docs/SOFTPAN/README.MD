> Historical vertical-only driver evidence. Use [PAN installation and controls](../PANNING.MD), [current native evidence](../QUAL/PAN/README.MD) and the [two-axis PCjr/ColorPlus install guide](RELEASE.MD) for the current release. These original test records remain unchanged.

# PCjr and ColorPlus software panning candidates

Public evidence copies omit host lease records, process identities and host
paths. Framebuffer dumps, guest logs and pixel verdicts retain their recorded
bytes. Private originals remain local.

Both candidates pass two Windows 3.0 real-mode sessions each. Each adapter
passes 64 full-frame cases: 4,096,000 pixels and 49,152 unused-bank bytes.
The cases cover viewport edges/clamping, drawing offscreen, DDB/DIB/text,
clipping, ScrollDC, cursor clipping/restore, drawing under the cursor,
helper start/follow/stop, repeated pans, normal exit and relaunch. Both
sessions start at viewport row zero. Forty measured pans allocate no
additional memory. Each fixture retains a 128-byte difference from entry.

JRPAN.DRV is 59,008 bytes; CPPAN.DRV is 58,864 bytes. Each uses a 64,000-byte
shadow, 32,000 more than the fixed profile. The PCjr measurement shell
leaves 339,488 bytes with the accepted fixed driver and 303,456 with the
panned build (two measurements each; the 36,032-byte total difference also
includes code/data). The ColorPlus full fixture starts with 314,528 bytes.

JRPAN-REVIEW.ZIP and CPPAN-REVIEW.ZIP are separate local installation
packets. Their INSTALL.TXT files give native Setup, helper startup and
rollback steps. The ColorPlus packet includes the byte-identical accepted
PCP3216.DRV as a separate fixed rollback choice and the owner's existing
CGA.GR2 support file. No complete OS media is included. Native Setup itself
is covered by the later [installation workflow](INSTALL.MD). The final
ColorPlus install packet is CPPAN-INSTALL.ZIP; its only payload change from
CPPAN-REVIEW.ZIP is the DOS 3.20-compatible ECHO OFF launcher line.

QUALIFY.JSON binds builds, apps, tests and packets. JR-RUN1/2.JSON and
CP-RUN1/2.JSON are pixel verdicts. JR-RAW.ZIP and CP-RAW.ZIP contain raw
dumps and logs. JR-CURSOR.PNG and CP-CURSOR.PNG are decoded VRAM captures;
CP-NATIVE.PNG is an actual 86Box framebuffer capture during the test.
JR-STAGE.JSON checks that the final compositor generates the built PCjr
assembly. CP-RAM.JSON and CP-RAM.ZIP preserve the additional 13 assembled
presenter cases (426,192 bytes compared, including guarded/clipped rows).

## Resolved ColorPlus test fixture failure

The earlier boot fixture stalled before SPTEST with both the accepted
fixed driver and the panning candidate. Read-only debugger samples showed
0000:003D while BIOS ticks advanced. The accepted fixed driver then booted
with the existing PC DOS 3.20 fixture and the same Windows support files.
The unchanged panning candidate passed both full sessions there. The
partition offset is 8,704 bytes; raw geometry is 615 cylinders, 4 heads,
17 sectors. CP-FIXTURE.JSON records the comparison. CP-START.PNG is the
historical pre-fix screen, not a current ColorPlus limitation.

The harness now reads geometry from the supplied DOS image and captures
closed session data on the host, avoiding the old DOS COPY-directory
syntax issue. No driver edit was needed to resolve the startup symptom.

All accepted packages and existing profiles remain unchanged. No physical
hardware, CF writes, publication or merge occurred.
