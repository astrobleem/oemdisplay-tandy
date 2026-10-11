# W31CHECK

W31CHECK is a host-side static screen for 16-bit Windows NE executables and
DLLs. It reads real NE headers, segment records, imported-name tables, module
references, entry points, export-name tables, and relocation records. It uses
Capstone in 16-bit x86 mode to decode reachable code from the module startup
entry and fixed NE entry points. It does not execute an input binary.

The tool is intentionally limited to the Windows 3.0 real-mode question. It
does not emulate Windows, prove that all code is reachable, or create a generic
compatibility database. Supply a complete, unmodified local Windows 3.0
directory with `--api-dir` to compare imported API names and ordinals against
that OS's NE exports. API files are read locally and are never copied into the
report or source tree.

The report separates the NE program-flags byte from the application-flags byte.
It records protected-mode-only and declared CPU flags without treating the
expected Windows version byte as proof of compatibility. Windows 386 targets,
286+/386 CPU declarations, protected-mode dependencies, and verified missing
Windows 3.0 imports are reported as blockers.

## Usage

```powershell
python tools/W31CHECK/w31check.py C:\private\CALC.EXE `
  --api-dir C:\private\windows-3.0 `
  --format markdown `
  --output C:\private\CALC-W31CHECK.md
```

Without `--api-dir`, imports remain unverified and the verdict cannot be
`CANDIDATE`. Ordinal imports remain displayed as `#N`; names are resolved only
from the actual Windows 3.0 NE export tables. The tool does not equate a
Windows-version flag with compatibility.

## Verdicts

- **BLOCKED**: a reachable instruction requires a newer CPU than the target;
  the image is marked protected-mode-only or targets another OS; or an import
  is absent from a supplied Windows 3.0 API module.
- **CANDIDATE**: the available static checks found no known blocker, the
  Windows 3.0 API references were resolved, and the module has a reachable
  code root. Reachability is incomplete, so runtime testing is still required.
- **UNKNOWN**: required reference evidence is unavailable, reachable code
  could not be decoded, dynamic API lookup makes the static import list
  incomplete, x87 instructions have no WIN87EM module reference, or the image
  asks for a later Windows version without runtime proof.
- **COMPATIBLE**: emitted only when a separate runtime-evidence JSON confirms
  real-mode Windows 3.0, an 8088, 640 KB, 320x200x16, real input, a
  representative task, redraw, and clean exit. Static analysis cannot emit
  this verdict by itself.

CPU incompatibility is reported from decoded instructions, not byte-pattern
searches. The report distinguishes those proven reachable instructions from
indirect calls/jumps, movable entry bundles, and code outside analyzed roots.
Those gaps remain incomplete evidence; they are not mislabeled as newer-CPU
instructions.

The optional runtime proof schema is:

```json
{
  "result": "PASS",
  "target": {
    "windows": "3.0",
    "mode": "real",
    "cpu": "8088",
    "memory_kb": 640,
    "display": "320x200x16"
  },
  "actions": {
    "input": true,
    "representative_task": true,
    "redraw": true,
    "clean_exit": true
  }
}
```

This schema is only an evidence gate. It does not automate a guest or make an
unverified claim about any application.

## Tests

```powershell
python -m unittest discover -s tools/W31CHECK -p "test_*.py" -v
```

The default suite builds original synthetic NE fixtures in memory for valid,
truncated, segment-boundary, name/ordinal import, internal-relocation,
missing-API, protected-mode, newer-CPU, and conservative code-reachability
cases. It has an opt-in host smoke test for private Windows 3.0 Calculator and
Notepad copies; the Windows executables are not included in the repository.
That smoke test is skipped unless both private-media paths are set:

```powershell
$env:W31CHECK_REAL_APPS_DIR = 'C:\private\w31check-apps'
$env:W31CHECK_WINDOWS_30_API_DIR = 'C:\private\windows-3.0'
python -m unittest discover -s tools/W31CHECK -p "test_*.py" -v
```

Capstone is the only third-party runtime dependency. Use the pinned version in
`requirements.txt`; do not fetch or install it automatically from the analyzer.
