#!/usr/bin/env python3
"""Compatibility entry for the shared queue/lifetime API-stub tests."""
from pathlib import Path
import subprocess,sys
subprocess.run([sys.executable,str(Path(__file__).resolve().parents[1]/'panui/KEYTEST.PY')]+sys.argv[1:],check=True)
