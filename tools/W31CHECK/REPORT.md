# W31CHECK compatibility evidence

## Scope and conclusion

W31CHECK is a host-side, read-only static screen for 16-bit Windows NE
executables and DLLs. It parses real NE headers, segments, module references,
import names and ordinals, entry points, name tables, and relocation records.
Capstone 5.0.7 decodes reachable code in x86 16-bit mode. The analyzer never
executes an input binary and does not infer compatibility from the Windows
version flag.

The Windows 3.11 OEM media contains Calculator and Notepad, originally stored
as KWAJ method-3 compressed files. A bounded local decoder produced files with
the declared lengths and valid MZ/NE headers. Updated fixup-aware analysis
still finds reachable 80186 instructions in both, so both are **BLOCKED** for
the 8088. Calculator also has one unverified `SHELL` module reference; Notepad
has unverified `COMMDLG` and `SHELL` references and dynamic API lookup. Those
uncertainties are separate from the CPU blockers.

The Windows 3.0 Calculator and Notepad baseline files have no detected
newer-CPU instructions, but neither is a static candidate after the fixup and
dynamic-lookup checks: Calculator has 472 relocation-affected instructions;
Notepad uses dynamic API lookup and has an overlapping/decode failure. No
Windows 3.0 app is currently supported as a first runtime candidate by this
report.

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
| `CALC.EXE` (43,072 bytes) | KERNEL, GDI, USER, WIN87EM, SHELL | 125 | 124 verified; 0 confirmed missing; `SHELL` module unverified | 8,431 | 292 | 14 | 1 | BLOCKED |
| `NOTEPAD.EXE` (32,736 bytes) | KERNEL, GDI, USER, KEYBOARD, COMMDLG, SHELL | 166 | 157 verified; 0 confirmed missing; `COMMDLG`/`SHELL` modules unverified | 7,269 | 672 | 0 | 4 | BLOCKED |

Both files target Windows NE, report expected Windows version flag `3.10`,
program flags `0x02`, and application flags `0x03`. The version flag does not
establish compatibility. The first detected newer-CPU instructions are
`CALC.EXE` segment 1 offset `0x0628` (`PUSH imm`) and `NOTEPAD.EXE` segment 1
offset `0x0C02` (`PUSH imm`). Immediate `PUSH`, immediate `IMUL`, and
immediate-count shifts are 80186 instructions, so these are concrete 8088
incompatibilities in reachable code.

The local Windows 3.0 reference confirms the listed imports but does not contain
the `SHELL` or `COMMDLG` modules. Those are unverified module references, not
confirmed missing imported APIs. Calculator's 14 reachable 8087 instructions
are accompanied by a `WIN87EM` module reference, but that does not prove the
software-emulation path works. Import-fixup instructions are counted separately
from relocation-affected instructions so imported API calls do not create a
false code-path uncertainty.

Full per-import names and ordinals, individual decoded instruction locations,
and reachability caveats are in the host-generated reports under private media
storage. No per-application result is hardcoded into the analyzer.

## Windows 3.11 CharMap reanalysis

The exact local `CHARMAP.EXE` decoded from Windows 3.11 OEM media is 22,016
bytes and declares Windows version flag `3.10`. Against the local Windows 3.0
NE export reference it imports 116 APIs: 115 are present and `GDI!#330` is
absent from the complete Windows 3.0 GDI entry table. The
[Wine Win16 GDI export specification](https://raw.githubusercontent.com/wine-mirror/wine/master/dlls/gdi.exe16/gdi.exe16.spec)
maps ordinal 330 to `EnumFontFamilies`. This compatibility reference supplies
the likely API name; the local Windows 3.0 export table is the evidence that
the ordinal is missing on the target. The analyzer reports CharMap **BLOCKED**
for that API dependency. It found no reachable newer-CPU instruction, so this
is an API blocker, not a CPU blocker.

The static scan decoded 4,375 reachable instructions and left 352 control-flow
edges unresolved, with one overlapping decode path. Dynamic import lookup is
also present. Those reachability limits remain visible; they do not change the
separate confirmed missing-API result. No guest was launched. The checked
Windows 3.0 GDI image is from the local reference directory and was not
modified.

## Windows 3.0 baseline analysis

| Local baseline file | Modules | Direct imports | Windows 3.0 API check | Reachable instructions | Unresolved edges | CPU blockers | 8087 ops | Static result |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- |
| `CALC.EXE` (40,480 bytes) | KERNEL, GDI, USER, WIN87EM | 120 | all verified; none missing | 7,246 | 731 | 0 | 0 | UNKNOWN |
| `NOTEPAD.EXE` (31,936 bytes) | KERNEL, GDI, USER, KEYBOARD | 186 | all verified; none missing | 7,527 | 485 | 0 | 0 | UNKNOWN |

Both Windows 3.0 baseline files have expected version flag 3.0, program flags
`0x02`, application flags `0x03`, and no reachable newer-CPU instruction
reported by Capstone. Calculator has 524 relocation-affected instructions,
which makes its static reachability uncertain. Notepad has dynamic API lookup
and one decode failure. Both remain **UNKNOWN**, despite complete direct-import
matches; neither is yet supported as a first runtime candidate. Their local
reports are retained in private media storage.

## Analyzer verdict rules

- **BLOCKED** means a specific incompatibility was found: a protected-mode-only
  flag or dependency, a non-Windows target, a declared 286+/386 CPU requirement,
  a reachable newer-CPU instruction, or an import proven absent from the
  supplied Windows 3.0 NE export reference.
- **CANDIDATE** means the available static evidence found no known blocker, the
  direct imports were verified, and there are no relocation-affected code
  paths, unresolved API lookups, or decode failures. Indirect control flow and
  code outside decoded roots remain incomplete.
- **UNKNOWN** means reference or reachability evidence is incomplete, dynamic
  API lookup prevents complete import checking, code fixups make an instruction
  or branch target uncertain, reachable bytes could not be decoded, a reachable
  x87 instruction lacks a `WIN87EM` module reference, or the version flag
  requests a later Windows version.
- **COMPATIBLE** requires separate passing runtime evidence for Windows 3.0
  real mode on an 8088 with 640 KB and 320x200x16, including input, a
  representative task, redraw, and clean exit. Evidence must also identify the
  exact host-side image by filename, size, and SHA-256; the hash is never
  published as an application result or used as a compatibility shortcut.

Newer-CPU incompatibility is derived from decoded instructions, not raw-byte
pattern searches. Non-additive relocation chains are followed; when a fixup
touches instruction code or a control-flow target, the affected path is marked
uncertain rather than treating raw file bytes as the loaded instruction. Static
reachability limits are reported separately.

## Validation and next experiment

The host suite covers malformed and truncated NE files, relocation chains and
cycles, unused and constant entry bundles, import relocations by name and
ordinal, Windows 3.0 export matching, protected-mode and VxD dependencies,
known later-CPU instructions and unknown instruction families, conservative
fixup reachability, and image-bound runtime-evidence validation. KWAJ tests
cover malformed headers and streams, declared-size bounds, oversized Huffman
trees, output overruns, trailing data, and MZ/NE output validation. Opt-in
media checks use the locally identified Windows 3.0 and Windows 3.11
Calculator/Notepad files and the local Windows 3.0 API reference.

The current source run was:

```text
python -m unittest discover -s tools/W31CHECK -p 'test_*.py' -v
Ran 46 tests in 1.560s
OK
```

This full run enabled the private-media Windows 3.0 app/reference checks and the
Windows 3.11 KWAJ media check. The default suite can skip local-media checks;
synthetic parser, disassembler, and KWAJ tests require no proprietary binaries.

Neither Windows 3.11 Calculator, Notepad, nor CharMap is eligible for the next
target trial: Calc and Notepad have reachable 80186 instructions, and CharMap
imports a Windows 3.0 API ordinal absent from the supplied GDI reference. The
Windows 3.0 baseline copies remain UNKNOWN for the reasons above. A later
host-side analysis should identify another candidate before requesting a
bounded guest slot. No guest was launched for this work.
