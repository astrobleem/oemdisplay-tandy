#!/usr/bin/env python3
"""Check renderer invariants in a temporary directory with GCC sanitizers."""
from pathlib import Path
import os,subprocess,tempfile
root=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='matrix-tests-') as tmp:
 exe=Path(tmp)/'TESTHOST'
 subprocess.run([os.environ.get('CC','gcc'),'-x','c','-std=c89','-O2',
                 '-fsanitize=undefined,address','-fno-pie','-no-pie',
                 str(root/'TESTHOST.C'),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True,env={**os.environ,'ASAN_OPTIONS':'detect_leaks=0'})
print('Matrix rendering host checks PASS')
