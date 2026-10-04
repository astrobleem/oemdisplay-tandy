#!/usr/bin/env python3
"""Run the portable C89 configuration checks from the source archive."""
from pathlib import Path
import os, subprocess, tempfile
root=Path(__file__).resolve().parents[2]
here=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='tstart10-config-') as work:
    exe=Path(work)/'testcfg'
    subprocess.run(['gcc','-x','c','-std=c89','-pedantic','-Wall','-Wextra','-Werror',
        '-fsanitize=address,undefined','-I',str(root),
        str(here/'TESTCFG.C'),str(root/'SCFGCORE.C'),'-o',str(exe)],check=True)
    env=os.environ.copy();env['ASAN_OPTIONS']='detect_leaks=0'
    subprocess.run([str(exe)],env=env,check=True)
