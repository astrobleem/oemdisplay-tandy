"""Prepare a private DIB-optimized core and matching DOS installers; no acceptance."""
from pathlib import Path
import argparse,hashlib,importlib.machinery,json,re,struct,zlib
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
P=importlib.machinery.SourceFileLoader('dib_pan_publisher',str(ROOT/'tools/PAN/PUBLISH.PY')).load_module()
S=importlib.machinery.SourceFileLoader('dib_pan_staging',str(ROOT/'tools/PAN/PREPARE.PY')).load_module()
N=S.N;C=P.C
CHANGED={'SETUP.EXE','WINXT/FIXXT.EXE','WINXT/HPXY.DRV'}

def identity(b):return dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def require(ok,msg):
 if not ok:raise ValueError(msg)
def emit(out,files):
 out.mkdir(parents=True,exist_ok=False)
 for n,b in files.items():
  p=out/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
def validate_driver(driver,build):
 require(build.get('build')=='PASS' and build.get('sha256')==identity(driver)['sha256'],'Driver/native build binding differs')
 P.native(driver,True)
 ne=struct.unpack_from('<I',driver,60)[0];count=struct.unpack_from('<H',driver,ne+28)[0];table=ne+struct.unpack_from('<H',driver,ne+34)[0]
 require(table+count*8<=len(driver),'Invalid NE segment table')
 gross=sum(struct.unpack_from('<H',driver,table+i*8+6)[0] or 65536 for i in range(count))
 require(gross==build['gross_NE_bytes'] and gross<=127531,'Driver allocation budget differs')
 require(build.get('presentation')=='Unchanged released converter; no solid predicate','Unreviewed presentation change')
 patch=ROOT/'src/hpxydib/DIB.PY'
 require(identity(patch.read_bytes())['sha256']==build['dib_overlay_sha256'],'DIB source/build binding differs')
 return gross
def compose(before,driver,fix,setup):
 after=dict(before);after.update({'SETUP.EXE':setup,'WINXT/FIXXT.EXE':fix,'WINXT/HPXY.DRV':driver})
 require(set(after)==set(before),'Consumer inventory changed')
 require({n for n in before if before[n]!=after[n]}==CHANGED,'Unexpected core payload changes')
 require(not any(n.upper().endswith(('.PY','.ZIP')) for n in after),'Consumer host preparation or nested archive')
 return after
def prepare(driver_path,build_path,out,watcom,commit):
 require(re.fullmatch('[0-9a-f]{40}',commit or ''),'Full source commit required')
 driver=driver_path.read_bytes();build=json.loads(build_path.read_bytes());gross=validate_driver(driver,build)
 # Validate the current accepted PAN producer before making any new output.
 q,packets=P.products();before=C.members(packets['WINXT.ZIP'])
 h={n:P.exact(row) for n,row in q['helpers'].items()}
 require(not out.exists(),'Fresh output directory required');out.mkdir(parents=True)
 native=out/'native';S.stage(native,h,watcom)
 N.write(native/'HPXYID.H','#ifndef HPXYID_H\n#define HPXYID_H\n#define HPXY_FILE "HPXY.DRV"\n#define HPXY_BYTES %dUL\n#define HPXY_CRC 0x%08xUL\n#endif\n'%(len(driver),zlib.crc32(driver)))
 fix=N.compile_native(native,watcom)
 N.aliases(native,dict(h,**{'FIXXT.EXE':fix,'CPSET.EXE':(ROOT/'tools/UPAN/BIN/CPSET.EXE').read_bytes(),'HPXY.DRV':driver}))
 setup=N.compile_native(native,watcom,'SETUP',True)
 files=compose(before,driver,fix,setup);archive=C.archive(files)
 emit(out/'expanded',files);(out/'WINXT.ZIP').write_bytes(archive)
 inputs={p.name:identity(p.read_bytes()) for p in native.iterdir() if p.suffix in ('.C','.H','.ASM')}
 receipt=dict(status='PREPARED_NOT_QUALIFIED',source_commit=commit,baseline_runtime_source=q['runtime_source'],baseline_archive=identity(packets['WINXT.ZIP']),archive=identity(archive),files={n:identity(b) for n,b in sorted(files.items())},changed=sorted(CHANGED),driver=identity(driver),gross_NE_bytes=gross,build=build,native_sources=inputs,installers={'SETUP.EXE':identity(setup),'FIXXT.EXE':identity(fix)},inherited_packets={n:identity(b) for n,b in packets.items() if n!='WINXT.ZIP'},gaps=['Independent review','Repeated native DIB/raster checks','Native FRESH, UPDATE and ordinary Windows Setup transactions','Installed PAN and Windows application acceptance','Final catalog and publication approval'])
 N.write(out/'PREPARE.JSN',json.dumps(receipt,indent=2)+'\n');return receipt
def main():
 a=argparse.ArgumentParser(description=__doc__)
 for n in ('driver','build','out','watcom'):a.add_argument('--'+n,type=Path,required=True)
 a.add_argument('--commit',required=True);v=a.parse_args();print(json.dumps(prepare(v.driver,v.build,v.out,v.watcom,v.commit),indent=2))
if __name__=='__main__':main()
