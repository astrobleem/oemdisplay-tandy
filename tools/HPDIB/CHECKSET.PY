"""Verify ordinary Windows Setup at the native pause before full repair."""
from pathlib import Path
import argparse,hashlib,json,re,sys
def setup_evidence(fs,expected):
 if not __debug__:raise RuntimeError('Native acceptance requires enabled assertions')
 assert fs.readbytes('DISPOK.TXT').strip()==b'DISPLAY_FINISHED'
 assert not fs.exists('RETURN1.TXT')
 log=fs.readbytes('DISPLAY.LOG');text=log.decode('ascii')
 match=re.search(r'Windows Setup returned status (-?\d+)\.',text);assert match
 status=int(match[1]);assert status in (0,1),'Untested Setup return status'
 replaced='HPXY updated. Other installed files and INI settings were not repaired.' in text
 if replaced:assert 'Replace only SYSTEM' in text
 else:assert 'The selected HPXY driver already matches; no replacement needed.' in text
 driver=fs.readbytes('WINDOWS/SYSTEM/HPXY.DRV');assert driver==expected
 ini=fs.readbytes('WINDOWS/SYSTEM.INI');assert re.search(rb'^display\.drv\s*=\s*HPXY\.DRV\s*$',ini,re.I|re.M)
 return log,driver,ini,status,replaced

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 for n in ('out','driver','deps'):ap.add_argument('--'+n,type=Path,required=True)
 v=ap.parse_args();out=v.out.resolve()
 if not __debug__:raise RuntimeError('Native acceptance requires enabled assertions')
 (out/'SETUP-WITNESS.JSN').write_text(json.dumps(dict(status='FAIL',reason='Setup checkpoint verification incomplete')))
 sys.path.insert(0,str(v.deps.resolve()))
 from pyfatfs.PyFatFS import PyFatFS
 def pin(b):return dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
 lease=json.loads((out/'FINAL-LEASE.JSON').read_text())
 assert lease.get('status')=='PASS' and lease.get('lease_acquired') is True and lease.get('lease_released') is True and lease.get('inventory_after')==[]
 assert lease.get('children') and all(c.get('stopped') is True for c in lease['children'])
 assert json.loads((out/'RUNTIME.JSON').read_text())['mode']==3
 screen=(out/'DOS-CURRENT.TXT').read_text(encoding='utf-8')
 assert 'HPDIB readback checkpoint before full repair.' in screen and 'Press any key' in screen
 with PyFatFS(str(out/'DISK.IMG'),offset=8704,read_only=True) as fs:
  log,driver,ini,status,replaced=setup_evidence(fs,v.driver.read_bytes())
 (out/'SETUP-PASS.LOG').write_bytes(log)
 r=dict(status='PASS_NATIVE_DISPLAY_ROUTE_BEFORE_REPAIR',installed_driver=pin(driver),pause_before_full_repair=True,setup_status=status,helper_replacement_used=replaced,setup_log=pin(log),system_ini=pin(ini),physical_hardware=False)
 (out/'SETUP-WITNESS.JSN').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))

if __name__=='__main__':main()
