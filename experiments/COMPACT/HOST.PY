"""Uppercase .PY discovery for compact tools on case-sensitive hosts.

Adapted from tools/XTFONTS/HOST.PY; MIT, Windows XT contributors.
"""
import importlib.machinery as machinery
from pathlib import Path
import runpy
import sys

HERE = Path(__file__).resolve().parent


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ('BUILD.PY', 'FONT.PY', 'TEST.PY', 'PREP.PY', 'HOSTGDI.PY'):
        raise SystemExit('HOST.PY BUILD.PY|FONT.PY|TEST.PY|PREP.PY|HOSTGDI.PY [arguments]')
    script = HERE / sys.argv[1]
    sys.path.insert(0, str(HERE))
    sys.path_importer_cache[str(HERE)] = machinery.FileFinder(str(HERE),
        (machinery.SourceFileLoader, machinery.SOURCE_SUFFIXES + ['.PY']),
        (machinery.SourcelessFileLoader, machinery.BYTECODE_SUFFIXES),
        (machinery.ExtensionFileLoader, machinery.EXTENSION_SUFFIXES))
    sys.argv = [str(script)] + sys.argv[2:]
    runpy.run_path(str(script), run_name='__main__')


if __name__ == '__main__':
    main()
