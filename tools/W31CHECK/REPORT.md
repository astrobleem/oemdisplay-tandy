# W31CHECK compatibility evidence

## Scope and conclusion

W31CHECK is a host-side, read-only static screen for 16-bit Windows NE
executables and DLLs. It parses real NE headers, segments, module references,
import names and ordinals, entry points, name tables, and relocation records.
Capstone 5.0.7 decodes reachable code in x86 16-bit mode. The analyzer never
executes an input binary and does not infer compatibility from the Windows
version flag.

The Windows 3.11 OEM media contains Calculator and Notepad, originally stored
as KWAJ method-3 compressed files. A small bounded local decoder was written
from the published format description after the installed decoders failed.
Both outputs match their declared lengths and contain valid MZ/NE headers.
W31CHECK reports reachable 80186 instructions in both apps, so both are
**BLOCKED** for the target 8088. Notepad also has more reachable 80186
instructions and more unresolved Windows 3.0 module imports; Calculator uses
8087 instructions. Neither is an eligible first Windows 3.11 candidate for the
Tandy 1000 EX.

As a separate Windows 3.0 baseline, Notepad remains the simpler later runtime
trial because it has no x87 instructions and fewer unresolved control-flow
edges than Calculator. That baseline finding is not a Windows 3.11 result.

## Existing repository experiments

The repository already has useful but narrower work:

- [`examples/TSHELL/EVIDENCE/NE.JSON`](../../examples/TSHELL/EVIDENCE/NE.JSON)
  records a manual NE inspection for the shell example.
- [`examples/TSHELL/DOS/NEWWIN.TXT`](../../examples/TSHELL/DOS/NEWWIN.TXT)
  preserves a loader failure and recovery diagnostic.
- [`examples/FILEDROP/SOURCE/RUNTEST.PY`](../../examples/FILEDROP/SOURCE/RUNTEST.PY)
  exercises the cross-drive, read-only file-drop path in a cloned guest.
- [`examples/COMMDLG/SOURCE/RUNTEST.PY`](../../examples/COMMDLG/SOURCE/RUNTEST.PY)
  and [`examples/COMMDLG/TESTS/BUILD.PY`](../../examples/COMMDLG/TESTS/BUILD.PY)
  cover the common-dialog experiment.
- [`examples/TSHELL/TESTS/RUNHOST.PY`](../../examples/TSHELL/TESTS/RUNHOST.PY)
  and `GRPTEST.PY` cover host-side shell checks.

I found no reusable parser that compares NE import relocations with actual
Windows 3.0 exports and disassembles reachable 16-bit code. W31CHECK fills that
gap without an application-specific compatibility table.

## Prior compatibility-list results

The local W3RMCSL 0.3 archive is readable. Its README identifies the release as
a proof of concept dated March 20, 2021. The creator describes a Windows 3.0a
86Box setup using an 8088, 640 KB, DOS 3.31, and separate CGA/VGA checks. The
creator's [project thread](https://www.vogons.org/viewtopic.php?t=80064)
reports 1,354 titles, 207 duplicates, and 220 entries marked not applicable.
For CGA it reports 237 OK, 77 SCREEN, 598 FAIL, and 15 not tested; for VGA it
reports 210 OK, 0 SCREEN, 544 FAIL, and 173 not tested. These are prior
86Box/Windows 3.0a results, not runs on the target Tandy 1000 EX.

The W3RMCSL ZIP contains calculator-like entries such as
`CICA9207/CHEMWIN/mmcalc.exe` (36,016 bytes, dated 1991-05-09),
`CICA9207/HPCALC/HPCALC.EXE` (34,576 bytes, dated 1990-10-25), and
`sms1.918/MORTCALC/MORTGAGE.EXE` (57,696 bytes, dated 1991-08-30), plus an
`HPCALC.ZIP` entry. It contains no exact Windows system `CALC.EX_` or
`NOTEPAD.EX_` entry. No archived application was executed or copied into this
repository.

## Windows 3.11 OEM media and decoding

The host archive `Microsoft Windows 3.11 (OEM) (3.5).7z` is 7,394,494 bytes.
Its six disk images are each 1,474,560 bytes. The FAT12 listing for `DISK4.IMG`
shows these exact files, both timestamped 1993-12-31 03:11:00:

| Archive entry | Compressed size | KWAJ header | Decoded output |
| --- | ---: | --- | ---: |
| `DISK4.IMG\CALC.EX_` | 25,112 bytes | method 3, data offset 27, flags `0x0019`, name `CALC.EXE` | 43,072 bytes |
| `DISK4.IMG\NOTEPAD.EX_` | 17,938 bytes | method 3, data offset 30, flags `0x0019`, name `NOTEPAD.EXE` | 32,736 bytes |

KWAJ method 3 is Jeff Johnson's LZ plus Huffman stream, not a normal LZH
archive. The [libmspack KWAJ format document](https://github.com/kyz/libmspack/blob/master/libmspack/doc/szdd_kwaj_format.html)
describes its fixed header, optional output-length/name fields, five Huffman
tables, and LZ ring buffer. The [libmspack method-3 decoder](https://github.com/kyz/libmspack/blob/master/libmspack/mspack/kwajd.c)
confirms that its KWAJ reader dispatches method 3 to a dedicated LZH decoder.
Those sources were read for format and support research; no libmspack code was
copied and no library or binary was downloaded or installed.

The installed 7-Zip 22.01 reports LZH support but no KWAJ format and rejects
both `.EX_` files as archives. The older installed 7-Zip 9.10 beta also has no
KWAJ format. Windows `expand.exe` copied each input byte-for-byte, preserving
the KWAJ signature; that output was treated as a failed decode. No local
libmspack or KWAJ-capable command was found.

`kwaj_method3.py` is an independent, standard-library-only decoder scoped to
KWAJ method 3. It requires a declared positive output length, limits inputs to
8 MiB and outputs to 16 MiB, bounds every header and bitstream read, rejects
malformed Huffman tables and output overruns, and refuses to overwrite an
existing output. It writes only after the decoded length matches and the bytes
pass MZ/NE signature and offset checks. The compressed originals and decoded
outputs remain in private host media storage; neither was added to this source
tree. Local hashes and extraction details are retained in a private provenance
record and are not part of publication.

No Windows application, setup program, archived utility, or guest was run.

## Windows 3.11 static comparison

The decoded files were analyzed against the locally available Windows 3.0 NE
export reference. `BLOCKED` means the disassembler found a reachable instruction
that the 8088 cannot execute. It does not mean every code path was reached; the
unresolved-edge and decode-failure counts below keep that uncertainty visible.

| App | Modules | Direct imports | Windows 3.0 API evidence | Reachable instructions | Reachable 80186 instructions | x87 ops | Decode failures | Unresolved edges | Verdict |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `CALC.EXE` (43,072 bytes) | KERNEL, GDI, USER, WIN87EM, SHELL | 125 | 124 verified; 0 confirmed missing; `SHELL` unverified | 9,048 | 292 | 126 | 1 | BLOCKED |
| `NOTEPAD.EXE` (32,736 bytes) | KERNEL, GDI, USER, KEYBOARD, COMMDLG, SHELL | 166 | 155 verified; 0 confirmed missing; 2 ordinals and COMMDLG/SHELL unverified | 7,269 | 672 | 0 | 4 | BLOCKED |

Both files target Windows NE, report expected Windows version flag `3.10`,
program flags `0x02`, and application flags `0x03`. The version flag does not
establish compatibility. The first detected newer-CPU instructions are
`CALC.EXE` segment 1 offset `0x0628` (`PUSH imm`) and `NOTEPAD.EXE` segment 1
offset `0x0C02` (`PUSH imm`). Immediate `PUSH`, immediate `IMUL`, and
immediate-count shifts are 80186 instructions, so these are concrete 8088
incompatibilities in reachable code.

The available Windows 3.0 exports confirm all checked imports. The reference
directory lacks `SHELL` and `COMMDLG`, so those module imports remain
unverified rather than being presented as confirmed missing APIs. Notepad has
two additional kernel ordinal imports the export parser cannot verify. These
API uncertainties do not remove the independent CPU blockers. Calculator's
126 x87 operations are accompanied by a `WIN87EM` module reference, but that
does not prove the software-emulation path works.

Full per-import names and ordinals, individual decoded instruction locations,
and reachability caveats are in the host-generated reports under private media
storage. No per-application result is hardcoded into the analyzer.

## Windows 3.0 baseline analysis

| Local baseline file | Modules | Direct imports | Windows 3.0 API check | Reachable instructions | Unresolved edges | CPU blockers | 8087 ops | Static result |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- |
| `CALC.EXE` (40,480 bytes) | KERNEL, GDI, USER, WIN87EM | 120 | all verified; none missing | 8,245 | 707 | 0 | 106 | CANDIDATE |
| `NOTEPAD.EXE` (31,936 bytes) | KERNEL, GDI, USER, KEYBOARD | 186 | all verified; none missing | 1,399 | 72 | 0 | 0 | CANDIDATE |

Both Windows 3.0 baseline files have expected version flag 3.0, program flags
`0x02`, application flags `0x03`, and no reachable newer-CPU instruction
reported by Capstone. Calculator's 8087 instructions and `WIN87EM` dependency
still require runtime validation. Notepad is the simpler Windows 3.0 baseline
trial because it has no x87 instructions and fewer reachable instructions and
unresolved edges. These are static candidates, not runtime successes.

## Analyzer verdict rules

- **BLOCKED** means a specific incompatibility was found: a protected-mode-only
  flag or dependency, a non-Windows target, a declared 286+/386 CPU requirement,
  a reachable newer-CPU instruction, or an import proven absent from the
  supplied Windows 3.0 NE export reference.
- **CANDIDATE** means the available static evidence found no known blocker and
  the direct imports were verified. Indirect control flow and code outside
  decoded roots remain incomplete.
- **UNKNOWN** means reference or reachability evidence is incomplete, dynamic
  API lookup prevents complete import checking, a reachable x87 instruction
  lacks a `WIN87EM` module reference, or the version flag requests a later
  Windows version.
- **COMPATIBLE** requires separate passing runtime evidence for Windows 3.0
  real mode on an 8088 with 640 KB and 320x200x16, including input, a
  representative task, redraw, and clean exit.

Newer-CPU incompatibility is derived from decoded instructions, not raw-byte
pattern searches. Static reachability limits are reported separately.

## Validation and next experiment

The host suite covers malformed and truncated NE files, import relocations by
name and ordinal, Windows 3.0 export matching, protected-mode and VxD
dependencies, known later-CPU instructions, incomplete control flow, and
runtime-evidence gating. KWAJ tests cover malformed headers and streams,
declared-size bounds, oversized Huffman trees, output overruns, trailing data,
and MZ/NE output validation. An opt-in media test checks the exact local
Windows 3.11 Calculator and Notepad identities.

The current source run was:

```text
python -m unittest discover -s tools/W31CHECK -p 'test_*.py' -v
Ran 33 tests in 0.836s
OK
```

The media and Windows 3.0 smoke tests are enabled when their three private-media
environment paths are set. The default suite can skip those local-media checks;
synthetic parser, disassembler, and KWAJ tests require no proprietary binaries.

Neither Windows 3.11 application is eligible for the target 8088 based on
reachable 80186 instructions. Do not use either for the next guest trial. A
later experiment should first select a different Windows 3.0/3.1 application
whose reachable code has no newer-CPU instruction and whose imports are
verified. Any runtime experiment still requires a bounded guest slot; no guest
was launched for this work.
