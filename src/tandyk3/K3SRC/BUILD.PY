#!/usr/bin/env python3
"""Run existing DOS Microsoft tools in DOSBox-X; no downloads or installation."""
import argparse, hashlib, json, os, struct, subprocess
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('--tools',type=Path,required=True)
p.add_argument('--dosbox',type=Path,required=True)
a=p.parse_args(); here=Path(__file__).resolve().parent
conf='''[sdl]
output=surface
[dosbox]
machine=tandy
memsize=16
[cpu]
core=normal
cputype=8086_prefetch
cycles=fixed 200000
[mixer]
nosound=true
[midi]
mididevice=none
[autoexec]
@echo off
mount C "{tools}"
mount D "{here}"
D:
BUILD.BAT
'''
(here/'BUILD.CNF').write_text(conf.format(tools=a.tools.resolve(),here=here))
env=os.environ.copy();env['SDL_VIDEODRIVER']='dummy';env['SDL_AUDIODRIVER']='dummy'
with (here/'HOST.LOG').open('wb') as f:
 subprocess.run([str(a.dosbox),'-nopromptfolder','-conf',str(here/'BUILD.CNF')],env=env,stdout=f,stderr=subprocess.STDOUT,timeout=120)
log=(here/'BUILD.LOG').read_text(errors='replace')
print(log)
if 'PASS' not in log:raise SystemExit('Build failed')
