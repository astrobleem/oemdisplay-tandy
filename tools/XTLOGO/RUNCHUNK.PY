"""Run one explicitly allocated bounded native chunk under the shared lock."""
import argparse
import csv
import datetime
import io
import json
import msvcrt
from pathlib import Path
import subprocess
import time

def conflicts():
    data=subprocess.check_output(['tasklist.exe','/FO','CSV','/NH'],text=True)
    return [row[:2] for row in csv.reader(io.StringIO(data)) if row and
            any(term in row[0].lower() for term in ('dosbox','86box','pcem','tandybox'))]
def run(workspace,config,purpose,seconds):
    if not 5<=seconds<=60:raise ValueError('One chunk must be bounded to 5..60 seconds')
    inputs=json.loads((workspace/'INPUTS.JSON').read_bytes())
    if conflicts():raise ValueError('Conflicting emulator; no launch')
    lock=Path(inputs['lock']).open('rb');process=None;held=False
    record={'purpose':purpose,'authorized_chunk_seconds':seconds,'config':str(config),
            'native_qualified':False,'conflicts_before':[]}
    start=time.monotonic()
    try:
        msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1);held=True
        if conflicts():raise ValueError('Conflicting emulator after acquiring lock')
        record['acquired_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
        si=subprocess.STARTUPINFO();si.dwFlags|=subprocess.STARTF_USESHOWWINDOW;si.wShowWindow=0
        with (workspace/(purpose+'.HOST.LOG')).open('wb') as log:
            process=subprocess.Popen([inputs['dosbox'],'-nopromptfolder','-conf',str(config)],
                cwd=config.parent,stdout=log,stderr=subprocess.STDOUT,startupinfo=si,
                creationflags=subprocess.CREATE_NO_WINDOW)
            record['pid']=process.pid
            while process.poll() is None and time.monotonic()-start<seconds-2:time.sleep(.2)
            record['exit_code']=process.poll()
    finally:
        if process and process.poll() is None:
            process.terminate()
            try:process.wait(timeout=2)
            except subprocess.TimeoutExpired:process.kill();process.wait(timeout=2)
            record['terminated_at_bound']=True
        if held:
            lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)
            record['released_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
        lock.close();record['seconds']=round(time.monotonic()-start,3)
        record['conflicts_after']=conflicts()
        (workspace/(purpose+'.STATUS.JSON')).write_bytes((json.dumps(record,indent=2)+'\n').replace('\n','\r\n').encode())
        print(json.dumps(record,indent=2),flush=True)
    if record.get('exit_code')!=0:raise ValueError('Native chunk failed or exceeded its bound')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--workspace',type=Path,required=True);p.add_argument('--config',type=Path,required=True)
    p.add_argument('--purpose',required=True);p.add_argument('--allocated-seconds',type=int,required=True)
    a=p.parse_args();run(a.workspace.resolve(),a.config.resolve(),a.purpose,a.allocated_seconds)
