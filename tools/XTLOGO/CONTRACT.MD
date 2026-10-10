# Static logo boundary (rc.5 baseline)

Baseline: v0.1.0-rc.5, commit 0c400228eede1b0aedde8c91c3598636b1ea7e1c.
This revision does not patch or redistribute Windows' loader. The accepted
independent slow wave, its compressed payload and wrapper remain unchanged.

## Verified inputs and concatenation

The qualified owned SYSTEM/WIN.CNF is 3,456 bytes, SHA-256
371bd1935f84505d61873f1e08a17b858d667a5149d71995d4285c6f17782bdb.
The old owned CGALOGO.LGO is 880 bytes, SHA-256
d9609adff83a63fda7a67e5e8cd7ed3dfb73f42e4d9971697fd43465231da807.
The existing original WXTSPL01.RLE is 4,062 bytes, SHA-256
eec3a413bb776bea8eccb19a379428d15f06cbdc0ac41b0871345ff9c24caf1c.
Saved native CGA, EGA and 160-mode installations byte-exactly establish:

    WIN.COM = WIN.CNF + CGALOGO.LGO + WXTSPL01.RLE (8,398 bytes)
    XTTEST.COM = WIN.CNF + original XTLOGO.LGO (39,427 bytes)

The proposed Setup route replaces only the middle component with XTSTATIC.LGO.
WXTSPL01.RLE keeps its distinct name and exact accepted original artwork bytes.
Windows Setup, not the DOS helpers, constructs installed WIN.COM.

## Loader ABI, verified by private disassembly and existing original module

WIN.CNF's COM-relative 0E4A routine enters the paragraph-aligned appended LGO
at offset 4 by a far call, with DS equal to the LGO segment. Four leading
bytes must be ASCII LOGO. Show returns by RETF; AX is the byte count copied
from LGO offset zero into the loader's resident area (COM offset 0240).
The loader later calls offset 7 of that relocated segment. Hide must therefore
be position-independent within the returned resident prefix. The original
independent wave returns 48 bytes; this replacement uses the same 48-byte
ceiling. No references to discarded show code, appended RLE or absolute
original segment are permitted in hide. Show preserves all caller registers
except its defined AX result and preserves flags and stack balance. Hide
preserves registers, flags and stack balance, including repeated calls.

The loader preserves/restores BIOS data-area 0040:0084 around show. It calls
hide on the ordinary zero-status kernel return. Its existing nonzero-status
branch skips hide and exits with zero; a logo module cannot repair that branch
without changing the loader or adding another caller. Missing kernel checks
normally precede show. These limits are retained, not hidden by a PASS claim.

## State, pixels and bounds

Normal qualified entry is BIOS text mode 3, page 0 after the existing RESERVE
guard. Other initial modes/pages refuse drawing and return a harmless resident
hide prefix. A valid show remembers mode 3 and switches to standard CGA BIOS
mode 6 (640x200, one bit per pixel), as the previous static path did. Writes
are confined to B800:0000..1F3F and B800:2000..3F3F; no extra Tandy video bank,
shadow surface, allocation, DOS/timer/IRQ hook, disk scan or SHA work is used.
Hide restores mode 3 once; its 0FFh state makes repeated hide harmless.
It does not promise to restore arbitrary screen contents, palette or page.

RLE begins immediately at the end of the emitted raw LGO. The supported
original-art format is a 62-byte BMP header: 640x200, planes=1, bpp=1,
compression=2, two black/white palette entries and exactly 4,000 payload bytes.
Encoded pairs only: nonzero count with value 00h or 11h; EOL 00 00 after
exactly 640 pixels; exactly 200 rows; final EOB 00 01 at byte 4,062. Absolute
runs and delta commands refuse. This deliberately implements the verified
original-art subset, not a general BMP decoder. Full validation precedes any
video change or framebuffer write. Every pair read and pixel address is
bounded. BMP rows are bottom-up; CGA rows use 80 bytes and two 8 KiB banks.
LGO+RLE and the complete COM must fit the 64 KiB COM address space.

## Test obligations and remaining dependencies

Host checks: deterministic assembly, header/resident size, 8086-only code,
RLE bounds/corruption, exact framebuffer pixels, show/hide register/flag/stack
contracts, relocated/repeated hide and unsupported-entry refusal. Native
checks require an allocated slot: Setup on five graphics profiles plus text
where feasible; static screenshot and GUI/exit; unchanged Color slow-wave
path; absent/corrupt payload failures; preparation default zero-SHA and optional
VERIFY; complete original-file rollback. Host pixels are specimens, not native
Windows screenshots. Qualification is pending until recorded native tests pass.

After successful integration, only CGA.GR2 remains a separately gathered owned
support file. Owned DOS/Windows and installed WIN.CNF, kernel, Setup and other
non-font Windows components remain required. Fonts and both logo renderers
are original redistributable assets. CGA.GR2/kernel/loader replacement is out
of scope. No publication or merge is authorized for this revision.
