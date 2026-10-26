"""Verify the independently reviewed CGA payload and public README derivation.

No compiler, installer, emulator or network access. Acceptance changes need
new native evidence and review; changing a catalog pin alone is insufficient.
"""
from pathlib import Path
import hashlib,io,json,re,struct,zipfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
def identity(b):return dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def members(b):
 with zipfile.ZipFile(io.BytesIO(b)) as z:
  names=z.namelist()
  if len(names)!=len(set(names)) or z.testzip():raise ValueError('Invalid CGA archive')
  return {n:z.read(n) for n in names}
def verify(data=None):
 record=json.loads((HERE/'ACCEPT.JSN').read_bytes())
 if record['status']!='NATIVE_EMULATION_QUALIFIED_INDEPENDENTLY_REVIEWED':raise ValueError('CGA acceptance missing')
 if data is None:data=(ROOT/record['path']).read_bytes()
 if identity(data)!=record['packet']:raise ValueError('CGA packet differs from accepted bytes')
 files=members(data)
 if {n:identity(b) for n,b in files.items()}!=record['members']:raise ValueError('CGA member inventory changed')
 if set(n.split('/')[0] for n in files)!={'SETUP.EXE','README.TXT','CGA'} or len(files)!=25:raise ValueError('CGA expanded layout changed')
 payload={n:b for n,b in files.items() if n.startswith('CGA/')}
 if len(payload)!=23 or any(not re.fullmatch(r'CGA/[A-Z0-9]{1,8}\.[A-Z0-9]{1,3}',n) for n in payload):raise ValueError('CGA DOS payload inventory invalid')
 if any(n.upper().endswith(('.ZIP','.PY')) for n in files):raise ValueError('Consumer preparation dependency')
 exe=files['SETUP.EXE']
 if exe[:2]!=b'MZ' or len(exe)<64:raise ValueError('Native DOS SETUP missing')
 last,pages=struct.unpack_from('<HH',exe,2)
 if pages*512-(512-last if last else 0)!=len(exe):raise ValueError('SETUP appended archive refused')
 for name,pin in record['evidence'].items():
  if identity((ROOT/name).read_bytes())!=pin:raise ValueError('Changed CGA evidence: '+name)
 review=json.loads((ROOT/'docs/QUAL/CGA/REVIEW.JSN').read_bytes())
 qualified=json.loads((ROOT/'docs/QUAL/CGA/FINAL.JSN').read_bytes())
 if review['outcome']!='NO_RESIDUAL_FINDINGS' or review['reviewed_final_source']!=record['source_checkpoint']:raise ValueError('Independent review binding invalid')
 if review['consumer']!=record['source_packet'] or qualified['packet']!=record['source_packet']:raise ValueError('Native/review packet binding invalid')
 bundle=members((ROOT/'docs/QUAL/CGA/REVIEW.ZIP').read_bytes())
 original=bundle['CGADEV.ZIP']
 if identity(original)!=record['source_packet']:raise ValueError('Original reviewed packet missing')
 old=members(original)
 if {n:b for n,b in files.items() if n!='README.TXT'}!={n:b for n,b in old.items() if n!='README.TXT'}:raise ValueError('Public packaging changed tested runtime')
 expected=old['README.TXT'].decode('ascii').replace('\r\r\n','\n').replace('\r\n','\n')
 expected=expected.replace('IBM CGA DISPLAY FOR WINDOWS 3.0 - DEVELOPMENT CANDIDATE','IBM CGA DISPLAY FOR WINDOWS 3.0').replace('Local development candidate, tested in Windows 3.0 real mode on IBM XT/CGA','Tested in Windows 3.0 real mode on IBM XT/CGA')
 if files['README.TXT']!=expected.replace('\n','\r\n').encode('ascii'):raise ValueError('Unexpected public README delta')
 return dict(packet=record['packet'],members=25,unchanged_native_and_support_members=24,independent_review=review['outcome'],physical_hardware=record['physical_hardware'])

if __name__=='__main__':print(json.dumps(verify(),indent=2))
