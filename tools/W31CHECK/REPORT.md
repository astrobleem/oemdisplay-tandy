# W31CHECK initial compatibility evidence

## Scope and conclusion

W31CHECK is a host-side, read-only static screen for 16-bit Windows NE
executables and DLLs. It parses actual NE headers, segments, module references,
import names and ordinals, entry points, name tables, and relocation records. It
uses Capstone 5.0.7 in x86 16-bit mode to inspect reachable code. It never runs
the input binary.

The exact Windows 3.11 OEM media archive is present locally. Its `DISK4.IMG`
contains `CALC.EX_` and `NOTEPAD.EX_`, but both are KWAJ-compressed files. The
only available host `expand.exe` copied them without decoding them, leaving the
`KWAJ` signature intact; the installed 7-Zip can list the archive and FAT12
image but cannot decode those inner files. No KWAJ-capable reader was found in
the existing local tools. Those two 3.11 applications therefore have **no
NE/API/disassembly verdict yet**, and this report does not choose a Windows
3.11 first candidate.

The separately available Windows 3.0 Calculator and Notepad copies are parsed
only as known-baseline evidence. Both receive static `CANDIDATE` results against
the local Windows 3.0 API reference. That means no known blocker was found in
the analyzed evidence; it is not a runtime success or a Windows 3.11 result.

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

I found no reusable parser that compares NE import relocations to actual
Windows 3.0 exports and disassembles reachable 16-bit code. W31CHECK fills that
gap without adding an application-specific compatibility table.

## Prior compatibility-list results

The local W3RMCSL 0.3 archive is readable. Its README identifies the release as
a proof of concept dated March 20, 2021. The creator describes a Windows 3.0a
86Box setup using an 8088, 640 KB, DOS 3.31, and separate CGA/VGA checks. The
creator's [project thread](https://www.vogons.org/viewtopic.php?t=80064)
reports 1,354 titles, 207 duplicates, and 220 entries marked not applicable.
For CGA it reports 237 OK, 77 SCREEN, 598 FAIL, and 15 not tested; for VGA it
reports 210 OK, 0 SCREEN, 544 FAIL, and 173 not tested. Those aggregate statuses
are prior 86Box/Windows 3.0a evidence, not a run on the target Tandy 1000 EX.

The W3RMCSL ZIP contains calculator-like entries such as
`CICA9207/CHEMWIN/mmcalc.exe` (36,016 bytes, dated 1991-05-09),
`CICA9207/HPCALC/HPCALC.EXE` (34,576 bytes, dated 1990-10-25), and
`sms1.918/MORTCALC/MORTGAGE.EXE` (57,696 bytes, dated 1991-08-30), plus an
`HPCALC.ZIP` entry. It contains no exact Windows system `CALC.EX_` or
`NOTEPAD.EX_` entry. No archived application was executed or copied into this
repository.

## Local media identities

The host archive `Microsoft Windows 3.11 (OEM) (3.5).7z` is 7,394,494 bytes.
Its six disk images are each 1,474,560 bytes. The FAT12 listing for `DISK4.IMG`
shows these exact files, both timestamped 1993-12-31 03:11:00:

| Archive entry | Stored size | Finding |
| --- | ---: | --- |
| `DISK4.IMG\CALC.EX_` | 25,112 bytes | KWAJ-compressed; not decoded |
| `DISK4.IMG\NOTEPAD.EX_` | 17,938 bytes | KWAJ-compressed; not decoded |

The original archive was left untouched. Only a private copy of `DISK4.IMG` and
the two compressed app files remain in the task workspace. No app, Windows
setup program, or archived utility was executed. The Windows 3.11 comparison is
blocked specifically at decoding these two compressed files with the approved
local tools available in this task.

The separately available Windows 3.0 media supplied uncompressed host copies
of `CALC.EXE` and `NOTEPAD.EXE`. Their private copies are 40,480 and 31,936
bytes, respectively. The supplied local Windows 3.0 API directory was read in
place and was not copied into the repository.

## Windows 3.0 baseline analysis

| Local baseline file | Modules | Direct imports | Windows 3.0 API check | Reachable instructions | Unresolved edges | CPU blockers | 8087 ops | Static result |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- |
| `CALC.EXE` (40,480 bytes) | KERNEL, GDI, USER, WIN87EM | 120 | all verified; none missing | 8,245 | 707 | 0 | 106 | CANDIDATE |
| `NOTEPAD.EXE` (31,936 bytes) | KERNEL, GDI, USER, KEYBOARD | 186 | all verified; none missing | 1,399 | 72 | 0 | 0 | CANDIDATE |

Both are Windows-target NE files with an expected Windows version flag of 3.0,
program flags `0x02`, application flags `0x03`, and no reachable newer-CPU
instruction reported by Capstone. Calculator uses 8087 instructions and imports
WIN87EM; the analyzer still does not prove that the emulator path works. There
were no decode failures in either file. Indirect control flow and other
unreachable code keep both results static candidates only.

For a later Windows 3.0 runtime baseline, Notepad is the simpler first object
because it has no 8087 instructions and fewer reachable instructions and
unresolved edges. This is not a Windows 3.11 candidate selection.

## Analyzer verdict rules

- **BLOCKED** means a specific incompatibility was found: protected-mode-only
  flags or dependencies, a non-Windows target, a declared 286+/386 CPU
  requirement, a reachable newer-CPU instruction, or a direct import absent
  from the supplied Windows 3.0 NE export reference.
- **CANDIDATE** means the supplied static evidence found no known blocker and
  the direct imports were verified. Indirect control flow and code outside
  decoded roots remain incomplete.
- **UNKNOWN** means the reference or reachability evidence is incomplete,
  dynamic API resolution prevents complete import checking, a reachable x87
  instruction lacks a WIN87EM module reference, or the version flag requests a
  later Windows version.
- **COMPATIBLE** requires a separate passing runtime record for real-mode
  Windows 3.0 on an 8088 with 640 KB and 320x200x16, including input, a
  representative task, redraw, and clean exit.

The expected Windows version flag is reported as metadata only. It cannot by
itself produce `CANDIDATE` or `COMPATIBLE`. Reachable 80186+/286+/386+
instructions are identified from decoded instructions, not raw-byte pattern
searches.

## Validation and remaining work

The final local host run was:

```text
python -m unittest discover -s tools/W31CHECK -p 'test_*.py' -v
Ran 25 tests in 0.476s
OK
```

That run set `W31CHECK_REAL_APPS_DIR` and
`W31CHECK_WINDOWS_30_API_DIR`, so the optional real-media smoke test ran against
the Windows 3.0 copies instead of being skipped. The default test run skips
that opt-in check when either private-media environment variable is absent; it
does not skip any synthetic parser or disassembly tests.

Not done: Windows 3.11 NE analysis, guest/runtime validation, or a Tandy slot
run. The next static step is to decode the exact 3.11 `CALC.EX_` and
`NOTEPAD.EX_` copies with an approved local KWAJ-capable tool and analyze their
NE imports and code. After that evidence identifies a target, the next runtime
experiment should use a disposable clean Windows 3.0 real-mode guest and
record input, one representative task, redraw, and clean exit. A bounded guest
slot is still required before launching that experiment.
