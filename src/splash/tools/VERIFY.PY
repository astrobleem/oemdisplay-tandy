#!/usr/bin/env python3
"""Verify custom RLE and optionally Windows Setup's installed WIN.COM."""
from pathlib import Path
import argparse,hashlib,json
import runpy
decode=runpy.run_path(str(Path(__file__).with_name("BUILD.PY")))["decode"]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('rle',type=Path);p.add_argument('--windows',type=Path);a=p.parse_args()
data=a.rle.read_bytes();_,report=decode(data);report['rle_sha256']=hashlib.sha256(data).hexdigest()
if a.windows:
 win=(a.windows/'WIN.COM').read_bytes();cnf=(a.windows/'SYSTEM'/'WIN.CNF').read_bytes();lgo=(a.windows/'SYSTEM'/'CGALOGO.LGO').read_bytes()
 assert len(cnf)==3456 and len(lgo)==880
 assert hashlib.sha256(lgo).hexdigest()=='d9609adff83a63fda7a67e5e8cd7ed3dfb73f42e4d9971697fd43465231da807'
 assert win==cnf+lgo+data,'WIN.COM does not contain the expected exact startup components'
 assert hashlib.sha256((a.windows/'SYSTEM'/'TANDY88.DRV').read_bytes()).hexdigest()=='ac1aadce894058ab6dbdeab2d2a3fd8673a8b4e78d8798198d295f61f32dafee'
 report.update(win_com_bytes=len(win),win_com_sha256=hashlib.sha256(win).hexdigest(),loader_offset=len(cnf),rle_offset=len(cnf)+len(lgo),stock_loader_and_driver_verified=True)
print(json.dumps(report,indent=2))
