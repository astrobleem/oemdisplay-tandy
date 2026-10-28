from pathlib import Path
import sys,subprocess,json
ROOT=Path(__file__).resolve().parent
jobs=[('cga100','native-low-01','--image=native-cga100-02/DISK.IMG'),('cga640','native-mono-01','--image=native-cga100-02/DISK.IMG','--install-guards'),('tandy','native-tandy-01'),('pan','native-pan-01','--image=native-tandy-01/DISK.IMG'),('cgapan','native-cgapan-01','--image=native-cga100-02/DISK.IMG'),('tandy6404','native-t6404-01','--image=native-tandy-01/DISK.IMG'),('cga320','native-cga320-01','--image=native-cga100-02/DISK.IMG')]
ui=json.loads((ROOT/'native-ui100-03/RESULT.json').read_bytes())
assert ui['status']=='PASS'and ui['owned_stopped']and ui['lease_released']and str(ui['inventory_after'])=='0','UI/cleanup acceptance is required before this batch'
for kind,out,*extra in jobs:
    state=json.loads((ROOT/'WORKSTATE.json').read_bytes());state.update(status='NATIVE_MATRIX',owned_run=out,queued_runner=None);(ROOT/'WORKSTATE.json').write_text(json.dumps(state,indent=2))
    subprocess.run([sys.executable,str(ROOT/'prepare_cube.py'),kind,out,*extra],cwd=ROOT,check=True)
    subprocess.run([sys.executable,str(ROOT/'run_cube.py'),out],cwd=ROOT,check=True)
    result=json.loads((ROOT/out/'RESULT.json').read_bytes())
    assert result['status']=='PASS'and result['owned_stopped']and result['lease_released']and str(result['inventory_after'])=='0'
    print('COMPLETED',kind,out,flush=True)
    state=json.loads((ROOT/'WORKSTATE.json').read_bytes());state.update(owned_run=None);state.setdefault('native_passes',[]).append(out);(ROOT/'WORKSTATE.json').write_text(json.dumps(state,indent=2))
