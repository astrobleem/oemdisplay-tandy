#!/usr/bin/env python3
"""Compatibility entry for the unified Win3/8086 helper build. Native compilation is not runtime acceptance."""
from pathlib import Path
import argparse,subprocess,sys
ROOT=Path(__file__).resolve().parents[2]
ap=argparse.ArgumentParser(description=__doc__)
for name in ('repo','dosbox','lease','out'):ap.add_argument('--'+name,type=Path,required=True)
ap.add_argument('--watcom',type=Path,default=Path('C:/WATCOM'))
a=ap.parse_args()
subprocess.run([sys.executable,str(ROOT/'tools/UPAN/BUILD.PY'),'--toolchain',str(a.repo),'--dosbox',str(a.dosbox),'--lease',str(a.lease),'--out',str(a.out),'--watcom',str(a.watcom)],check=True)
