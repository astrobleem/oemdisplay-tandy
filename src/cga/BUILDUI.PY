#!/usr/bin/env python3
"""Compatibility entry for the unified Win3/8086 helper build. Native compilation is not runtime acceptance."""
from pathlib import Path
import argparse,subprocess,sys
ROOT=Path(__file__).resolve().parents[2]
ap=argparse.ArgumentParser(description=__doc__)
for name in ('repo','dosbox','lease','out'):ap.add_argument('--'+name,type=Path,required=True)
ap.add_argument('--watcom',type=Path,default=Path('C:/WATCOM'))
for name in ('wdesk','placement'):ap.add_argument('--'+name,type=Path,required=True)
a=ap.parse_args()
for source,names in ((a.wdesk,('WDCORE.C','WDCORE.H','WDWIN.C','WDWIN.H')),
                     (a.placement,('WTPLACE.C','WTPLACE.H'))):
 for name in names:
  current=ROOT/('src/wdesk/PLACE' if name.startswith('WTPLACE') else 'src/wdesk')/name
  if (source/name).read_bytes()!=current.read_bytes():ap.error('Review the changed shared workspace source first: '+name)
subprocess.run([sys.executable,str(ROOT/'tools/UPAN/BUILD.PY'),'--toolchain',str(a.repo),'--dosbox',str(a.dosbox),'--lease',str(a.lease),'--out',str(a.out),'--watcom',str(a.watcom)],check=True)
