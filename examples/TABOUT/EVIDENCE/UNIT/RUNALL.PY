#!/usr/bin/env python3
"""Execute the native harness in isolated pre-cloned guests; never run production guests."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import subprocess,json,shutil,hashlib
base=Path('/workspace/scratch/a84592844d2c');unit=base/'about-unit';runner=base/'tandy-about/src/tandysw/ROUNDGO.PY'
modes=['160','3204','6404','6402','baseline']
def run(mode):
 d=unit/mode;shutil.copyfile(unit/'ABOUTUT.EXE',d/'guest/ABOUTUT.EXE')
 p=subprocess.run(['python3',str(runner),str(d/'RUN.CNF'),str(d/'guest/ABOUTUT.LOG'),'--host-log',str(d/'HOST.LOG'),'--timeout','120'],capture_output=True,text=True)
 (d/'RESULT.JSON').write_text(p.stdout)
 record=json.loads(p.stdout) if p.stdout.strip() else {'complete':False,'stderr':p.stderr}
 record['mode']=mode;log=(d/'guest/ABOUTUT.LOG').read_text(errors='replace') if (d/'guest/ABOUTUT.LOG').exists() else ''
 record['pass_count']=sum(l.startswith('PASS=') for l in log.splitlines());record['failures']=[l[5:] for l in log.splitlines() if l.startswith('FAIL=')]
 record['screen']={k:int(v) for k,v in (l.split('=',1) for l in log.splitlines() if l.startswith(('SCREEN_WIDTH=','SCREEN_HEIGHT=','WIN_FLAGS=','CLIENT_WIDTH=','CLIENT_HEIGHT=','COLORS=','PLANES=','BITS=','VERSION=','FREE_BYTES=','FONT_WIDTH=','FONT_HEIGHT=')))}
 record['expected_screen']=dict(zip(('SCREEN_WIDTH','SCREEN_HEIGHT','COLORS','PLANES','BITS'),{'160':(160,200,16,4,1),'3204':(320,200,4,4,1),'6404':(640,200,4,4,1),'6402':(640,200,2,4,1),'baseline':(320,200,16,4,1)}[mode]))
 record['screen_matches']=all(record['screen'].get(k)==v for k,v in record['expected_screen'].items())
 record['pass']=record['screen_matches'] and record['complete'] and not record['failures'] and record['pass_count']==138
 print(mode,json.dumps(record),flush=True);return record
with ThreadPoolExecutor(max_workers=5) as ex:results=list(ex.map(run,modes))
summary={'production_source_sha256':hashlib.sha256((unit/'SUBJECT.C').read_bytes()).hexdigest(),'executable_sha256':hashlib.sha256((unit/'ABOUTUT.EXE').read_bytes()).hexdigest(),'total_checks':sum(x['pass_count'] for x in results),'pass':all(x['pass'] for x in results),'results':results,'limits':['Native Win16 execution in DOSBox-X 8086_prefetch with 640 KB and no EMS/XMS/UMB; not physical hardware.','Harness includes an exact source snapshot and calls real routines with synthetic messages; production WM_CREATE, WM_SIZE, WM_PAINT, WM_COMMAND and keyboard helpers execute against real Windows controls.','All pages, control geometry and font metrics are checked; these are not screenshots or full visual pixel comparisons.']}
(unit/'RESULTS.JSON').write_text(json.dumps(summary,indent=2)+'\n')
raise SystemExit(not summary['pass'])
