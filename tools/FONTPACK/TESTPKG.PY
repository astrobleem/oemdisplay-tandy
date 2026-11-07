"""Verify font packet closure against native compile inputs and frozen payloads."""
from pathlib import Path
import argparse,ast,hashlib,importlib.machinery,re,zipfile,zlib
HERE=Path(__file__).resolve().parent
P=importlib.machinery.SourceFileLoader('fontpack_check_stage',str(HERE/'PREPARE.PY')).load_module()
# Accepted native preparation/finisher, transaction and installed-GUI/font gates.
# Original OS Setup wizard completion is separately incomplete.
ACCEPTED='66cc8ab2a5a6061e4f55931d5123a010d427afc34a419dc5b9d3d3d2aef3cefa'

def check(archive,native=HERE/'NATIVE',candidate=False):
 raw=archive.read_bytes()
 if not candidate:assert ACCEPTED is not None and hashlib.sha256(raw).hexdigest()==ACCEPTED,'Not the qualified font archive'
 with zipfile.ZipFile(archive) as z:
  names=z.namelist();assert len(names)==len(set(names)) and z.testzip() is None
  body={n:z.read(n) for n in names}
 expected=P.payload();assert set(body)==set(expected),'Unexpected or missing consumer file'
 for n,b in expected.items():
  if n not in ('SETUP.EXE','WINXT/FIXXT.EXE'):assert body[n]==b,n
 for n in ('SETUP.EXE','WINXT/FIXXT.EXE'):assert body[n][:2]==b'MZ',n
 for n in ('SETUP.EXE','WINXT/FIXXT.EXE'):
  assert b'TINYXT_FONT_CORRUPT_STAGE' not in body[n] and b'TINYXT_FONT_CORRUPT_COMMIT' not in body[n],'Private fault hook leaked into '+n
 for n in ('SETUP.EXE','FIXXT.EXE'):
  built=native/n
  if candidate:assert built.is_file(),'Candidate validation needs final native build: '+n
  if built.is_file():assert body[n if n=='SETUP.EXE' else 'WINXT/'+n]==built.read_bytes(),'Packaged executable differs from final native build: '+n
 pins=(native/'SETPINS.H').read_text();rows=re.findall(r'^\{"((?:[^"\\]|\\.)+)","([a-f0-9]{64})",(\d+)UL,0,0x([a-f0-9]+)UL\}',pins,re.M)
 assert len(rows)==len(set(r[0] for r in rows))==len(body)-2,'Malformed/duplicate/unpinned payload'
 for name,sha,size,crc in rows:
  n=ast.literal_eval('"'+name+'"').replace('\\','/');b=body['WINXT/'+n]
  assert (len(b),hashlib.sha256(b).hexdigest(),zlib.crc32(b))==(int(size),sha,int(crc,16)),name
 with P.zipfile.ZipFile(P.ROOT/'tools/SAVPACK/BIN/WINXT.ZIP') as z:
  previous={n:z.read(n) for n in z.namelist()}
 changed={n for n in previous if body[n]!=previous[n]}
 assert changed==P.CHANGED,changed
 for name in names:
  assert all(re.fullmatch(r'[A-Z0-9_]{1,8}(\.[A-Z0-9]{1,3})?',part) for part in name.split('/')),name
 fontfiles={n for n in body if n.startswith('WINXT/FONTS/') and n.endswith('.FON')}
 assert fontfiles=={'WINXT/FONTS/'+n for n in P.FONTS}
 assert b'CAUTION:' in body['WINXT/FONTS/README.TXT'] and b'Helv' in body['WINXT/FONTS/README.TXT']
 print('PASS:',len(body),'members; exact source payload closure, native pin bindings, unchanged historical bytes, notices and optional font inventory.')
 print('Archive',len(raw),'bytes; SHA256',hashlib.sha256(raw).hexdigest())
if __name__=='__main__':
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('--archive',type=Path,default=HERE/'BIN/WINXT.ZIP');a.add_argument('--native',type=Path,default=HERE/'NATIVE');a.add_argument('--candidate',action='store_true');v=a.parse_args();check(v.archive,v.native,v.candidate)
