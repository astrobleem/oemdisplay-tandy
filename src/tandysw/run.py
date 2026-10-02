#!/usr/bin/env python3
"""Launch an existing Windows 3.0 guest prepared as described in README."""
from pathlib import Path
import subprocess, sys
if len(sys.argv)!=3: raise SystemExit("usage: run.py GUEST_DRIVE_C DOSBOX_X")
guest=Path(sys.argv[1]).resolve(); dosbox=Path(sys.argv[2]).resolve()
if not (guest/"WINDOWS"/"WIN.COM").exists(): raise SystemExit("Expected GUEST_DRIVE_C/WINDOWS/WIN.COM")
cfg=Path(__file__).resolve().parent/"TANDY.LOC"
cfg.write_text("[sdl]\nautolock=false\nfullscreen=false\noutput=surface\n[dosbox]\ntitle=Tandy Windows 3.0 V1\nallow more than 640kb base memory=true\nmemsize=16\nmachine=tandy\n[cpu]\ncputype=386\ncore=normal\ncycles=100000\n[serial]\nserial1=serialmouse\n[render]\nscaler=normal2x\n[autoexec]\n@ECHO OFF\nMOUNT C \""+str(guest)+"\"\nC:\nSET PATH=C:\\WINDOWS;Z:\\\nSET TEMP=C:\\WINDOWS\\TEMP\nCD WINDOWS\nWIN /R\n")
raise SystemExit(subprocess.call([str(dosbox),"-nopromptfolder","-conf",str(cfg)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL))
