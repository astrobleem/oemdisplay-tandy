#!/usr/bin/env python3
"""Focused shared-driver consumers; Windows GCC always uses the checked launcher."""
from pathlib import Path
import os
import subprocess
import sys
import tempfile

here = Path(__file__).resolve().parent
repo = here.parents[1]
flags = ['-x', 'c', '-std=c89', '-Wall', '-Wextra', '-Werror',
         '-Wno-cast-function-type', '-Wno-unused-function', '-I'+str(here)]
if os.name == 'nt':
    launcher = Path(r'C:\Users\chad\Documents\Codex\toolchains\gcc-ucrt64.py')
    compiler = [sys.executable, str(launcher), '--']
else:
    compiler = [os.environ.get('CC', 'gcc')]
for relative in ('examples/TSHELL/PSGOWN.H', 'tools/WHEEL/WIN16/SOURCE/TP/PSGOWN.H'):
    assert (repo/relative).read_bytes() == (here/'PSGOWN.H').read_bytes()
cases = [('TESTOWN', here/'TESTOWN.C', []),
         ('TESTTP', here/'TESTTP.C', []),
         ('TESTBOOT', repo/'examples/TSHELL/TESTS/TESTBOOT.C',
          ['-I'+str(repo/'examples/TSHELL/TESTS/HSTINC')])]
with tempfile.TemporaryDirectory(prefix='sound-owner-') as temp:
    for name, source, extra in cases:
        exe = Path(temp)/(name+'.exe')
        subprocess.run(compiler+flags+extra+[str(source), '-o', str(exe)], check=True)
        subprocess.run([str(exe)], check=True)
print('PASS: three shared-driver consumer suites')
