"""Private PR151 + compact XY overlay builder. Requires the pinned external build view.

Windows host only. The shared emulator lock is mandatory and nonblocking.
This builds no installer, touches no CF, and requires a fresh output folder.
"""
from pathlib import Path
import argparse,importlib.machinery,sys,json,shutil,hashlib,struct,subprocess,msvcrt,os

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo',type=Path,required=True,help='Pinned external source/toolchain view')
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--dosbox',type=Path,required=True)
    p.add_argument('--lease',type=Path,required=True,help='Shared emulator-lock file')
    p.add_argument('--sync-output','--batch',dest='batch',action='store_true',help='Opt-in synchronous narrow Output flushes; accepted packages stay unchanged')
    a=p.parse_args();repo=a.repo.resolve();out=a.out.resolve()
    sys.path.insert(0,str(repo/'src/tandysw'))
    patcher=importlib.machinery.SourceFileLoader('xypatch',str(Path(__file__).with_name('XRPATCH.PY'))).load_module()
    b=importlib.machinery.SourceFileLoader('xybuild',str(repo/'src/tandysw/BUILD88.PY')).load_module()
    prepare,run=b.baseline.prepare,b.bounded_run;state={}
    def prep(repo,out):
        r,s=prepare(repo,out);state.update(renderer=r,resources=s);return r,s
    def invoke(*args,**kw):
        if not state.get('patched'):
            patcher.patch(state['renderer'],batch=a.batch);state['patched']=True
        return run(*args,**kw)
    b.baseline.prepare,b.bounded_run=prep,invoke
    original=subprocess.Popen
    class HiddenPopen(original):
        def __init__(self,*args,**kw):
            si=subprocess.STARTUPINFO();si.dwFlags|=subprocess.STARTF_USESHOWWINDOW;si.wShowWindow=0
            kw['startupinfo']=si;kw['creationflags']=kw.get('creationflags',0)|subprocess.CREATE_NO_WINDOW
            super().__init__(*args,**kw)
    subprocess.Popen=HiddenPopen
    sys.argv=['BUILD88.PY','--repo',str(repo),'--out',str(out),'--dosbox',str(a.dosbox.resolve()),'--mode','320x200x16','--ui-profile','compact320']
    with a.lease.open('rb') as f:
        f.seek(0);msvcrt.locking(f.fileno(),msvcrt.LK_NBLCK,1)
        try:
            count=subprocess.check_output(['powershell.exe','-NoProfile','-Command','@(Get-Process -Name dosbox-x,dosbox,86Box,pcem,tandybox,FIXBOX -ErrorAction SilentlyContinue).Count'],text=True).strip()
            if count!='0':raise RuntimeError('Emulator already active; nothing launched')
            b.main()
        finally:
            f.seek(0);msvcrt.locking(f.fileno(),msvcrt.LK_UNLCK,1)
    shutil.copyfile(out/'TANDY88.DRV',out/'HPXY.DRV')
    raw=(out/'HPXY.DRV').read_bytes();ne=struct.unpack_from('<I',raw,0x3c)[0]
    count=struct.unpack_from('<H',raw,ne+0x1c)[0];off=ne+struct.unpack_from('<H',raw,ne+0x22)[0]
    gross=sum(struct.unpack_from('<H',raw,off+i*8+6)[0] or 65536 for i in range(count))
    assert gross-102955<=24576,('incremental budget',gross)
    baseline=out/'RESULT.json';baseline.rename(out/'BASEPIPE.json')
    report=dict(build='PASS',runtime='NOT_TESTED_BY_BUILD',candidate=('PRIVATE HPXY PR155 synchronous narrow Output' if a.batch else 'PRIVATE HPXY bounded Output rows (PR151)'),batching=False,synchronous_output=a.batch,logical=[640,256,16],viewport=[320,200,16],shadow_bands=[64000,17920],stage_bytes=1440,hardware_default=False,physical_tested=False,gross_NE_bytes=gross,delta_from_R3_gross_bytes=gross-102955,ceiling_delta=24576,sha256=hashlib.sha256(raw).hexdigest(),baseline_pipeline_report='BASEPIPE.json describes transformations before the XY overlay; its mode and optimization descriptions are not final XY behavior')
    baseline.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))
if __name__=='__main__':main()
