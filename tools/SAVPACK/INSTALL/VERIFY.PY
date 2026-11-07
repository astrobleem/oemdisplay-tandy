"""Verify completed private native installer cases; no emulator invocation."""
from pathlib import Path
import argparse,importlib.machinery,re,zlib
ROOT=Path(__file__).resolve().parent.parent
M=importlib.machinery.SourceFileLoader('fixture_prepare',str(Path(__file__).with_name('PREPARE.PY'))).load_module()

def verify(candidate,fixtures):
 rows=re.findall(r'^\{"([^"]+)","([^"]+)",(\d+)UL,(\d+)\}',(candidate/'native/SETFILES.H').read_text(),re.M)
 crcs=[int(x,16) for x in re.findall(r'^\s*0x([0-9a-f]+)UL,',(candidate/'native/SETINPUT.H').read_text(),re.M)]
 for case in ('UPDATE','FRESH','MIGRATE'):
  guest=fixtures/case/'guest'
  assert (guest/'DONE.TXT').read_text().strip()=='PASS',case+' native script failed'
  setup=(candidate/'native/SETUP.C').read_text();count=re.search(r'#define '+('FRESH' if case=='FRESH' else 'UPDATE')+r'_COUNT (\d+)',setup)[1]
  assert 'preparation: '+count+' verified files.' in (guest/'PREP.LOG').read_text(),case+' preparation count'
  assert 'Owned entries and cheap payload samples match.' in (guest/'CHECK2.LOG').read_text(),case+' final CHECK'
  assert 'need FIXXT REPAIR' in (guest/'MISSING.LOG').read_text(),case+' missing Cube CHECK did not reject'
  checked=0
  for (dest,name,size,kind),crc in zip(rows,crcs):
   dest=dest.replace('\\\\','/')
   if case!='FRESH' and dest.startswith('W30/'):continue
   p=guest/dest;assert p.exists(),(case,dest)
   if kind=='0':
    expected=candidate/'expanded/WINXT'/name
    assert p.read_bytes()==expected.read_bytes(),(case,dest,'payload differs')
   elif kind=='1':
    assert len(p.read_bytes())==int(size) and zlib.crc32(p.read_bytes())==crc,(case,dest,'Windows source differs')
   checked+=1
  assert checked==int(count),(case,checked,count)
  for n in ('CUBE.EXE','ORBITS.EXE','MATRIX.EXE','STARFLD.EXE'):
   assert (guest/'WINXT'/n).read_bytes()==(candidate/'expanded/WINXT'/n).read_bytes(),(case,n)
  for n in ('TSHELL.EXE','TSINPUT.DLL'):
   assert (guest/'WINDOWS'/n).read_bytes()==(candidate/'expanded/WINXT'/n).read_bytes(),(case,n)
  assert not (guest/'WINXT/MAZE.EXE').exists() and not (guest/'WINXT/FILES/MAZE.EXE').exists(),case+' Maze payload'
  for log in ('CPAPPLY','CPCHECK','CPREADY'):assert (guest/(log+'.LOG')).exists(),(case,log)
  assert 'Tandy Computer entry already registered; active selections preserved.' in (guest/'CPAPPLY.LOG').read_text(),case+' CPSET APPLY'
  metadata=(guest/'WINDOWS/SYSTEM/SETUP.INF').read_bytes()
  expected=b'CPLEAN1\r\nC:\\WINDOWS\\SYSTEM\\SETUP.INF\r\n'+str(len(metadata)).encode('ascii')+b'\r\n'
  assert (guest/'WINDOWS/SYSTEM/CPREADY.OK').read_bytes()==expected,case+' CPSET exact ready marker'
  if case=='MIGRATE':
   expected_size=int(re.search(r'#define SETUP_BYTES (\d+)',setup)[1])
   assert len(metadata)==expected_size,(case,'metadata migration size')
  ini=(guest/'WINDOWS/TSHELL.INI').read_bytes()
  if case!='FRESH':assert ini==M.CUSTOM,'Custom update settings changed'
  else:
   assert ini==(candidate/'expanded/WINXT/TSHELL.INI').read_bytes(),'Fresh seed changed'
   assert b'IdleSeconds=300\r\n' in ini and b'Maze' not in ini
  print(case,'PASS:',checked,'prepared paths verified; INSTALL/CHECK/missing-Cube rejection/REPAIR/CHECK; installed quartet, CPSET APPLY/CHECK/READY marker and settings correct.')

if __name__=='__main__':
 a=argparse.ArgumentParser()
 for n in ('candidate','fixtures'):a.add_argument('--'+n,type=Path,required=True)
 v=a.parse_args();verify(v.candidate,v.fixtures)
