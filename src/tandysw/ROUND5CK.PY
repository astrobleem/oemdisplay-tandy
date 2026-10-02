#!/usr/bin/env python3
"""Check measured Windows heap stability across 64 direct DIB blits."""
import argparse, hashlib, json
from pathlib import Path

def main():
 ap=argparse.ArgumentParser();ap.add_argument('guest',type=Path);ap.add_argument('--out',type=Path,default=Path('FINAL055.json'));a=ap.parse_args();values={}
 for line in (a.guest/'ROUND5.LOG').read_text().splitlines():
  k,v=line.split('=',1);values.setdefault(k,[]).append(int(v))
 same=(a.guest/'R5BEFORE.BIN').read_bytes()==(a.guest/'R5AFTER.BIN').read_bytes()
 report={'guest':str(a.guest),'driver_sha256':hashlib.sha256((a.guest/'WINDOWS/SYSTEM/TANDY88.DRV').read_bytes()).hexdigest(),'measurements':values,'framebuffer_before_after_identical':same}
 report['pass']=values.get('COMPLETE')==[1] and values.get('WARMUP_CALLS')==[8] and values.get('CALLS')==[16,32,48,64] and values.get('CALL_FAILURES')==[0] and all(v==values['LARGEST_BEFORE'][0]for v in values['LARGEST_AFTER']) and all(v==values['FREE_BEFORE'][0]for v in values['FREE_AFTER']) and same
 a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));return int(not report['pass'])
if __name__=='__main__':raise SystemExit(main())
