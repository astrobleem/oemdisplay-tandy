#!/usr/bin/env python3
"""Compile/run the shared C89 maze rules and renderer regression on a host C compiler."""
import argparse, os, subprocess, tempfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--cc',default=os.environ.get('CC','cc'));p.add_argument('--sanitize',action='store_true');a=p.parse_args()
with tempfile.TemporaryDirectory(prefix='maze-test-') as tmp:
 out=Path(tmp)/'mazetest'
 flags=['-fsanitize=address,undefined'] if a.sanitize else []
 subprocess.run([a.cc,'-x','c','-DHOSTMAIN','-std=c89','-Wall','-Wextra']+flags+[str(Path(__file__).with_name('TEST.C')),'-o',str(out)],check=True)
 env=os.environ.copy();env.setdefault('ASAN_OPTIONS','detect_leaks=0')
 subprocess.run([str(out)],check=True,env=env)
