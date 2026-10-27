"""Read back stopped native installation, real BMP round trip and clean lifecycle."""
from pathlib import Path
import sys,json,hashlib,struct,importlib.machinery,argparse,re
root=Path(__file__).resolve().parents[2]
if not __debug__:raise RuntimeError('Native acceptance requires enabled assertions')
ap=argparse.ArgumentParser(description=__doc__)
for n in ('out','driver','packet','deps'):ap.add_argument('--'+n,type=Path,required=True)
ap.add_argument('--case',choices=('full_finisher','ordinary_setup','combined'),required=True)
v=ap.parse_args();out=v.out.resolve();case=v.case;application=case!='ordinary_setup';sys.path.insert(0,str(v.deps.resolve()))
# Invalidate any prior verdict before imports/readback can fail.
(out/'INSTALLED.JSN').write_text(json.dumps(dict(status='FAIL',reason='Native installation verification incomplete')))
from pyfatfs.PyFatFS import PyFatFS
P=importlib.machinery.SourceFileLoader('installed_pan_reference',str(root/'tools/PAN/PUBLISH.PY')).load_module()
def pin(b):return dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def bmp(b):
 assert b[:2]==b'BM';off=struct.unpack_from('<I',b,10)[0];size=struct.unpack_from('<I',b,14)[0]
 if size==12:w,h,planes,bits=struct.unpack_from('<HHHH',b,18);compression=0;colors=1<<bits;palstart=26;psize=3
 else:
  assert size>=40;w,h,planes,bits,compression=struct.unpack_from('<iiHHI',b,18);colors=struct.unpack_from('<I',b,46)[0] or (1<<bits);palstart=14+size;psize=4
 assert planes==1 and 0<w<=4096 and 0<abs(h)<=4096 and bits in (1,4,8,24)
 palette=[tuple(reversed(b[palstart+i*psize:palstart+i*psize+3])) for i in range(colors)] if bits<24 else []
 height=abs(h);pitch=((w*bits+31)//32)*4;rgb=[]
 if compression==0:
  for y in range(height):
   row=(height-1-y if h>0 else y)*pitch+off
   for x in range(w):
    if bits==24:rgb.append(tuple(reversed(b[row+x*3:row+x*3+3])))
    else:
     v=(b[row+x] if bits==8 else (b[row+x//2]>>(0 if x&1 else 4))&15 if bits==4 else (b[row+x//8]>>(7-x%8))&1);rgb.append(palette[v])
 else:
  assert compression in (1,2) and bits==(8 if compression==1 else 4);indices=[[0]*w for _ in range(height)];x=y=0;i=off
  def put(v):
   nonlocal x;assert 0<=x<w and 0<=y<height;indices[y][x]=v;x+=1
  while i<len(b):
   n,v=b[i:i+2];i+=2
   if n:
    for j in range(n):put(v if bits==8 else ((v&15) if j&1 else v>>4))
   elif v==0:x=0;y+=1
   elif v==1:break
   elif v==2:x+=b[i];y+=b[i+1];i+=2
   else:
    length=v if bits==8 else (v+1)//2
    for j in range(v):put(b[i+j] if bits==8 else ((b[i+j//2]&15) if j&1 else b[i+j//2]>>4))
    i+=length+(length&1)
  rgb=[palette[v] for row in reversed(indices) for v in row]
 return w,height,rgb
lease=json.loads((out/'FINAL-LEASE.JSON').read_text())
children=lease.get('children')
if not (lease.get('status')=='PASS' and lease.get('lease_acquired') is True and lease.get('lease_released') is True and lease.get('inventory_after')==[] and isinstance(children,list) and children and all(type(c.get('pid')) is int and c['pid']>0 and c.get('stopped') is True for c in children)):
 raise ValueError('Native installation lifecycle incomplete')
assert json.loads((out/'RUNTIME.JSON').read_text())['mode']==3
assert (out/'CROOT/RETURN1.TXT').read_text().strip()=='RETURNED'
control=json.loads((out/'RESULT.JSN').read_text());assert control['outcome']=='PASS_NATIVE_HPXY_SINGLE_APP' and not control.get('error')
if application:
 for label,x,y in [('RIGHT',16,4),('DOWN',16,8),('HOME',0,0)]:
  state=(out/('PBRUSH_PAN_'+label+'.TXT')).read_text()
  assert re.search(r'^XYSTATE x=%d y=%d .*mode=1$'%(x,y),state,re.M),label
  assert r'cls=pbParent text=Paintbrush - C:\DIBOUT.BMP' in state,label
before=json.loads((out/'INSTALL-INPUT.JSN').read_text());assert before['driver_not_injected'] and before['previous_installed_driver_sha256']=='c86a243c9e724401de3fa40d2c304bb6e336c6f8ad5df241c2e4ff1911d297a9'
base,_=P.products();observed={}
with PyFatFS(str(out/'DISK.IMG'),offset=8704,read_only=True) as fs:
 driver=fs.readbytes('WINDOWS/SYSTEM/HPXY.DRV');assert driver==(v.driver).read_bytes()
 for n,row in base['helpers'].items():
  b=fs.readbytes('WINDOWS/'+('SYSTEM/' if n.endswith('.DLL') else '')+n);assert b==P.exact(row),n;observed[n]=pin(b)
 repair=fs.readbytes('REPAIR.LOG').decode('latin1') if application else ''
 if application:assert 'Repair complete. Run C:\\STARTXT' in repair
 if application:
  source=fs.readbytes('DIBTEST.BMP');saved=fs.readbytes('DIBOUT.BMP');assert bmp(source)==bmp(saved),'Paintbrush RGB round trip differs'
  (out/'DIBTEST.BMP').write_bytes(source);(out/'DIBOUT.BMP').write_bytes(saved);(out/'REPAIR.LOG').write_text(repair)
 assert fs.readbytes('WINXT/FIXXT.EXE')==(v.packet/'WINXT/FIXXT.EXE').read_bytes()
r=dict(status='PASS_NATIVE_INSTALLED_HPXY_DIB',route=case,normal_dos_return=True,installed_driver=pin(driver),installed_helpers=observed,driver_not_injected=True,normal_packet_path=True,pan_controls_pass=True,full_repair_invoked=application,repair_complete=True if application else None,paintbrush_tested=application,paintbrush_rgb_equal=True if application else None,native_controls=control,physical_hardware=False)
if application:r.update(bitmap_width=bmp(saved)[0],bitmap_height=bmp(saved)[1],input_bitmap=pin(source),output_bitmap=pin(saved))
if case in ('ordinary_setup','combined'):
 witness=json.loads((out/'SETUP-WITNESS.JSN').read_text())
 assert witness['status']=='PASS_NATIVE_DISPLAY_ROUTE_BEFORE_REPAIR' and witness['installed_driver']==pin(driver) and witness['pause_before_full_repair'] is True
 assert witness.get('setup_status') in (0,1) and type(witness.get('helper_replacement_used')) is bool
 assert pin((out/'SETUP-PASS.LOG').read_bytes())==witness['setup_log']
 if case=='ordinary_setup':
  boot=json.loads((out/'ORDINARY-BOOT-INPUT.JSN').read_text());assert boot['full_repair_invoked'] is False and boot['only_host_changed_guest_file']=='AUTOEXEC.BAT'
  assert 'FIXXT' not in boot['launcher'].upper() and 'DISPWIN.BAT' in boot['launcher'].upper()
  assert boot['protected_windows_files']['WINDOWS/SYSTEM/HPXY.DRV']==pin(driver)
  assert boot['setup_checkpoint']==pin((out/'SETUP-WITNESS.JSN').read_bytes()) and boot['setup_lease']==pin((out/'SETUP-LEASE.JSON').read_bytes())
  prior=json.loads((out/'SETUP-LEASE.JSON').read_text());assert prior['status']=='PASS' and prior['lease_acquired'] is True and prior['lease_released'] is True and prior['inventory_after']==[] and prior['children'] and all(isinstance(c,dict) and type(c.get('pid')) is int and c['pid']>0 and c.get('stopped') is True for c in prior['children'])
  ui=json.loads((out/'SETUP-UI.JSN').read_text());assert ui['status']=='OBSERVED_WINDOWS_SETUP_COMPLETE_CHANGES_FLOW' and ui['raw_keys']==pin((out/'RAWKEYS-LOG.JSON').read_bytes())
  for name,row in ui['frames'].items():assert row['identity']==pin((out/name).read_bytes())
  assert len(ui['frames'])==3
  keys=json.loads((out/'RAWKEYS-LOG.JSON').read_text());assert not any('{ESC}' in x.get('text','') or '{F3}' in x.get('text','') or any(k in (1,61) for k in x.get('taps',[])) for x in keys)
  r['setup_ui_observations']=ui
  r['ordinary_boot_without_full_repair']=True;r['installation_lease']=prior;r['boot_input']=boot
 r['native_windows_setup_completed']=True;r['setup_return_status']=witness['setup_status'];r['display_helper_replacement']=witness['helper_replacement_used'];r['setup_witness']=witness
(out/'INSTALLED.JSN').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
