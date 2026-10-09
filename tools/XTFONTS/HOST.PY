"""Run the preserved uppercase .PY font tools on Windows or case-sensitive hosts.

MIT, Copyright (c) 2026 Windows XT contributors. This changes Python source
discovery only; glyphs, serialization and native runtime bytes are untouched.
"""
import importlib.machinery as machinery
from pathlib import Path
import runpy
import sys

HERE=Path(__file__).resolve().parent

def main():
    if len(sys.argv)<2:
        raise SystemExit('Usage: HOST.PY BUILD.PY|TEST.PY|PUBLISH.PY [arguments]')
    script=HERE/sys.argv[1]
    if script.parent!=HERE or script.suffix!='.PY' or script.name=='HOST.PY' or not script.is_file():
        raise SystemExit('Choose an existing uppercase .PY tool in XTFONTS')
    for folder in (HERE,HERE.parent/'FLASHDISK'):
        sys.path.insert(0,str(folder))
        sys.path_importer_cache[str(folder)]=machinery.FileFinder(str(folder),
            (machinery.SourceFileLoader, machinery.SOURCE_SUFFIXES+['.PY']),
            (machinery.SourcelessFileLoader, machinery.BYTECODE_SUFFIXES),
            (machinery.ExtensionFileLoader, machinery.EXTENSION_SUFFIXES))
    sys.argv=[str(script)]+sys.argv[2:]
    runpy.run_path(str(script),run_name='__main__')

if __name__=='__main__':main()
