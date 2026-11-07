"""Synthetic effect-checker sensitivity and independent native-input model tests."""
from pathlib import Path
import ctypes,json,runpy,subprocess,tempfile,struct,argparse
HERE=Path(__file__).resolve().parent;F=runpy.run_path(str(HERE/'FXCHECK.PY'))
def fixture(root,candidate,quick=True):
 rows=['VERSION=2 EFFECTS=5 DENSITY=16 PHASES=%d GRID=%s CAPS=8 FRAME_BYTES=32768 FRAMES_PER_CASE=4'%(4 if quick else 8,'Q' if quick else 'FULL')];raw=bytearray();case=0
 for e,phase,index,count in F['records'](quick):
  o=F['shape'](e,phase,index,count);color=o[5];physical=15 if color==6 else color+1
  prefix=bytes(F['C']['rgb'](physical)+[physical|[32,0,0,0,0,0,0,0,0,0,16,16,0,16,16,48][physical]])+struct.pack('<6H',0,0xe117,1,0,0,0x3cc3)
  admit=int(o[4]==0 and (candidate or physical==15));value=F['RGB'][color][0]+(F['RGB'][color][1]<<8)+(F['RGB'][color][2]<<16)
  rows.append('CASE=%d EFFECT=%d PHASE=%d INDEX=%d COUNT=%d CX=%d CY=%d RX=%d RY=%d ANGLE=%d COLOR=%d AX=%d AY=%d HASH=%d RGB=%d PREFIX=%s RET=1 ERASE_RET=1 ACCEPTED=%d ERASE_ACCEPTED=%d RESYNC_ACCEPTED=0 RESYNC2_ACCEPTED=0 RESYNC=1 RESYNC2=1'%((case,e,phase,index,count)+o+(F['vertex_hash'](o),value,prefix.hex(),admit,admit)))
  for part in range(4):
   raw.extend(struct.pack('<2H',case,part));raw.extend(struct.pack('<HBHB',1,1,32767,0) if part<2 else struct.pack('<HB',32768,0))
  case+=1
 rows+=['CASES=%d FAILURES=0'%case,'COMPLETE=1'];root.mkdir();(root/'FXPRO.LOG').write_text('\n'.join(rows)+'\n');(root/'FXPRO.RLE').write_bytes(raw)
def check():
 count=0
 with tempfile.TemporaryDirectory() as td:
  root=Path(td);src=root/'geometry.c';src.write_text('#define _far\n#include "OVALFX.H"\nvoid model(int e,int p,int i,int n,int w,int h,FXOval *o){fxShape(e,p,i,n,w,h,o);}\nunsigned short hash(const FXOval *o){int k,x,y;unsigned short v=0;for(k=0;k<=32;k++){fxVertex(o,k,&x,&y);v=v*33U+(unsigned short)x;v=v*33U+(unsigned short)y;}return v;}\n');so=root/'geometry.so';subprocess.run(['gcc','-std=c89','-pedantic-errors','-O2','-shared','-fPIC','-I'+str(HERE),str(src),'-o',str(so)],check=True)
  class Oval(ctypes.Structure):_fields_=[(n,ctypes.c_int) for n in ['cx','cy','rx','ry','angle','color','aspectX','aspectY']]
  lib=ctypes.CDLL(str(so));lib.model.argtypes=[ctypes.c_int]*6+[ctypes.POINTER(Oval)];lib.hash.argtypes=[ctypes.POINTER(Oval)];lib.hash.restype=ctypes.c_ushort
  for w in [160,320,640]:
   for h in [100,200,400,480]:
    for n in [2,4,8,16]:
     for e in range(5):
      for p in range(64):
       for i in range(F['slots'](e,n)):
        o=Oval();lib.model(e,p,i,F['slots'](e,n),w,h,ctypes.byref(o));got=tuple(getattr(o,k) for k,_ in o._fields_);expected=F['shape'](e,p,i,F['slots'](e,n),w,h);assert got==expected,(e,p,i,n,w,h,got,expected);assert lib.hash(ctypes.byref(o))==F['vertex_hash'](expected);count+=1
  for quick in [True,False]:
   a=root/('a'+str(quick));b=root/('b'+str(quick));fixture(a,False,quick);fixture(b,True,quick);assert F['check'](a,b)['pass']
  a=root/'aTrue';b=root/'bTrue';log=b/'FXPRO.LOG';raw=b/'FXPRO.RLE';original=log.read_text();data=raw.read_bytes();rejections=0
  for mode in ['geometry','hash','admission','pixel','trailing','truncate']:
   log.write_text(original);raw.write_bytes(data)
   if mode=='geometry':log.write_text(original.replace('CX=160','CX=161',1))
   if mode=='hash':
    lines=original.splitlines();m=__import__('re').search(r'HASH=(\d+)',lines[1]);lines[1]=lines[1].replace(m[0],'HASH='+str(int(m[1])+1));log.write_text('\n'.join(lines)+'\n')
   if mode=='admission':log.write_text(original.replace('ACCEPTED=1 ERASE_ACCEPTED=1','ACCEPTED=0 ERASE_ACCEPTED=0',1))
   if mode=='pixel':v=bytearray(data);v[6]^=1;raw.write_bytes(v)
   if mode=='trailing':raw.write_bytes(data+b'BAD')
   if mode=='truncate':raw.write_bytes(data[:-1])
   try:F['check'](a,b)
   except ValueError:rejections+=1
   else:raise AssertionError('Mutation escaped: '+mode)
 return {'pass':True,'independent_C_vs_Python_geometry_and_WORD_vertex_hash_cases':count,'complete_synthetic_grids':[68,832],'deliberate_failures_detected':rejections,'scope':'host arithmetic/checker proof, synthetic pixels; NOT native GDI/colors/lifecycle/mode proof'}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--report',type=Path,required=True);a=p.parse_args();r=check();a.report.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
