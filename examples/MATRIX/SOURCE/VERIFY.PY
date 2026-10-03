#!/usr/bin/env python3
"""Validate completed RUNLAB outputs against host packing and exit evidence."""
from pathlib import Path
import argparse, hashlib, json, os, re, subprocess
p=argparse.ArgumentParser();p.add_argument('--runs',required=True,help='Prefix before -160-C, -160-Q and -XT-160 run directories');p.add_argument('--suffix',default='');p.add_argument('--exe',type=Path,required=True);p.add_argument('--host-test',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
sha=hashlib.sha256(a.exe.read_bytes()).hexdigest();result={'exe_sha256':sha,'modes':{},'xt':{},'caveat':'DOSBox-X 240-cycle approximate XT preset is not calibrated physical 8088 timing. Timer updates are completed animation advances, not monitor refreshes.'}
def run(mode,action):
 d=Path(a.runs+'-'+mode+'-'+action+a.suffix);r=json.loads((d/'RESULT.JSON').read_text());assert r['complete'] and r['exe_sha256']==sha;return d,r
for mode,w,k in [('160',160,0),('baseline',320,0),('3204',320,1),('6404',640,2),('6402',640,3)]:
 d,stats=run(mode,'C');q,qs=run(mode,'Q');qa=(q/'guest/MATRIX.LOG').read_text();assert qa.count('changed_screen_bytes=0 active_ok=1')==11;assert 'QA repair=PASS' in qa and 'QA DONE' in qa
 expected=a.out/('ORACLE-'+mode+'.RAW');subprocess.run([str(a.host_test.resolve()),str(expected),str(w),str(k)],env={**os.environ,'ASAN_OPTIONS':'detect_leaks=0'},stdout=subprocess.DEVNULL,check=True)
 raw=(d/'guest/MATRIX.RAW').read_bytes();exp=expected.read_bytes();banks=4 if mode in ('baseline','6404') else 2;pitch=160 if banks==4 else 80
 errors=sum(raw[(y%banks)*8192+(y//banks)*pitch+x]!=exp[(y%banks)*8192+(y//banks)*pitch+x] for y in range(200) for x in range(pitch));assert errors==0
 line=[l for l in stats['native_log'].splitlines() if l.startswith('END ')][0];numbers={key:int(value) for key,value in re.findall(r'(\w+)=(\d+)',line)};assert numbers['free_warm']==numbers['free_end'] and numbers['ticks']==60
 result['modes'][mode]={'frame40_mismatched_bytes':errors,'restoration_checks':11,'repaint_repair':True,'metrics':numbers}
for mode in ['160','6404']:
 d=Path(a.runs+'-XT-'+mode+a.suffix);r=json.loads((d/'RESULT.JSON').read_text());assert r['complete'] and r['exe_sha256']==sha;line=[l for l in r['native_log'].splitlines() if l.startswith('END ')][0];numbers={key:int(value) for key,value in re.findall(r'(\w+)=(\d+)',line)};assert numbers['ticks']==60 and numbers['free_warm']==numbers['free_end'];numbers['updates_per_second']=round(numbers['ticks']*1000/numbers['elapsed_ms'],3);result['xt'][mode]=numbers
f=Path(a.runs+'-F-160'+a.suffix);fr=json.loads((f/'RESULT.JSON').read_text());assert fr['complete'] and fr['exe_sha256']==sha and 'fast=0' in fr['native_log'];result['forced_gdi_completed']=True
(a.out/'RESULT.JSON').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
