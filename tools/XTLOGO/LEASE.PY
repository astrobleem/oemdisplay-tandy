"""Hold one allocated native lease, execute bounded queued private jobs, release."""
import argparse,csv,datetime,io,json,msvcrt
from pathlib import Path
import subprocess,time
def conflicts(exclude=None):
    data=subprocess.check_output(['tasklist.exe','/FO','CSV','/NH'],text=True)
    return [r[:2] for r in csv.reader(io.StringIO(data)) if r and r[1]!=str(exclude) and
            any(t in r[0].lower() for t in ('dosbox','86box','pcem','tandybox'))]
def run(workspace,deadline=None,minutes=None):
    inputs=json.loads((workspace/'INPUTS.JSON').read_bytes());queue=workspace/'QUEUE';queue.mkdir(exist_ok=True)
    status={'deadline_utc':deadline.isoformat() if deadline else None,'jobs':[],'native_qualified':False}
    lease=Path(inputs['lock']).open('rb');held=False;process=None
    def save():
        (workspace/'LEASE.JSON').write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8')
    def stop():
        nonlocal process
        if process and process.poll() is None:
            process.terminate()
            try:process.wait(timeout=2)
            except subprocess.TimeoutExpired:process.kill();process.wait(timeout=2)
        code=process.poll() if process else None
        process=None
        return code
    try:
        # Boundedly wait for somebody else's lease/process, never touch it.
        wait_end=time.monotonic()+30
        if deadline:wait_end=min(wait_end,time.monotonic()+max(0,(deadline-datetime.datetime.now(datetime.timezone.utc)).total_seconds()))
        while time.monotonic()<wait_end:
            if not conflicts():
                try:msvcrt.locking(lease.fileno(),msvcrt.LK_NBLCK,1);held=True;break
                except OSError:pass
            time.sleep(1)
        if not held:raise RuntimeError('Busy shared lease/emulator; no launch')
        if conflicts():raise RuntimeError('Conflicting emulator after lease acquisition')
        if minutes:
            deadline=datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(minutes=minutes)
            status['deadline_utc']=deadline.isoformat();status['allocated_minutes_from_acquisition']=minutes
        status['acquired_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();status['active']='idle';save()
        print('LEASE ACQUIRED '+status['acquired_utc'],flush=True)
        seen=set()
        while datetime.datetime.now(datetime.timezone.utc)<deadline:
            if (workspace/'STOP.LEASE').exists():break
            if (workspace/'PAUSE.LEASE').exists():time.sleep(.2);continue
            jobs=[p for p in sorted(queue.glob('*.JSON')) if p.name not in seen]
            if not jobs:time.sleep(.2);continue
            p=jobs[0];seen.add(p.name);job=json.loads(p.read_bytes());seconds=min(60,int(job['seconds']))
            if conflicts():raise RuntimeError('Conflicting emulator before job; no launch')
            cfg=Path(job['config']).resolve();assert cfg.is_relative_to(workspace)
            left=(deadline-datetime.datetime.now(datetime.timezone.utc)).total_seconds()
            if left<seconds+3:raise RuntimeError('Insufficient allocated time for bounded job')
            rec={'purpose':job['purpose'],'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
            status['active']=job['purpose'];status['jobs'].append(rec);save()
            si=subprocess.STARTUPINFO();si.dwFlags|=subprocess.STARTF_USESHOWWINDOW;si.wShowWindow=0
            start=time.monotonic()
            with (workspace/(job['purpose']+'.HOST.LOG')).open('wb') as log:
                process=subprocess.Popen([inputs['dosbox'],'-nopromptfolder','-conf',str(cfg)],cwd=cfg.parent,
                    stdout=log,stderr=subprocess.STDOUT,startupinfo=si,creationflags=subprocess.CREATE_NO_WINDOW)
                rec['pid']=process.pid;save()
                while process.poll() is None and time.monotonic()-start<seconds-2:
                    if conflicts(process.pid):raise RuntimeError('Other emulator appeared; stopping only our process')
                    time.sleep(.3)
                rec['exit_code']=process.poll();rec['seconds']=round(time.monotonic()-start,3)
                rec['stop_reason']='individual_timeout' if rec['exit_code'] is None else 'process_exited'
                rec['exit_code_after_stop']=stop()
            required=[Path(n) for n in job.get('require_nonempty',[])]
            if any(not p.is_file() or not p.stat().st_size for p in required):
                status['paused_reason']='Missing guest completion evidence after '+job['purpose']
                (workspace/'PAUSE.LEASE').write_text(status['paused_reason'])
            status['active']='idle';save();print('JOB '+json.dumps(rec),flush=True)
    except Exception as e:
        status['error']=str(e);print('LEASE ERROR '+str(e),flush=True)
    finally:
        stop()
        if held:
            lease.seek(0);msvcrt.locking(lease.fileno(),msvcrt.LK_UNLCK,1)
            status['released_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
        lease.close();status['active']='released';status['conflicts_after']=conflicts();save()
        print('LEASE RELEASED '+json.dumps(status),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workspace',type=Path,required=True)
    group=p.add_mutually_exclusive_group(required=True)
    group.add_argument('--deadline');group.add_argument('--minutes',type=int)
    a=p.parse_args()
    if a.minutes and not 1<=a.minutes<=15:p.error('Allocated duration must be 1..15 minutes')
    run(a.workspace.resolve(),datetime.datetime.fromisoformat(a.deadline) if a.deadline else None,a.minutes)
