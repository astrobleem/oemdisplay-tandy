"""Check the exact native-qualified combined package without OS media or emulation."""
from pathlib import Path
import argparse,hashlib,re,zipfile,zlib
HERE=Path(__file__).resolve().parent
ACCEPTED='fa5b55806d35d0aca9cb6c3a67b608866a169843769d4e7b54628317214376aa'
def check(archive,native=HERE/'NATIVE'):
 data=archive.read_bytes()
 assert hashlib.sha256(data).hexdigest()==ACCEPTED,'Not the native-qualified archive'
 with zipfile.ZipFile(archive) as z:
  names=z.namelist()
  assert len(names)==len(set(names)) and z.testzip() is None,'Duplicate or corrupt ZIP entry'
  body={n:z.read(n) for n in names}
 pins=(native/'SETPINS.H').read_text()
 rows=re.findall(r'^\{"([^"\n]+)","([0-9a-f]{64})",(\d+)UL,0,0x([0-9a-f]+)UL\}',pins,re.M)
 assert rows and len(rows)==len(re.findall(r'^\{"',pins,re.M))
 assert len(rows)==len({r[0] for r in rows})
 assert set(body)=={'SETUP.EXE','README.TXT'}|{'WINXT/'+r[0] for r in rows},'Unexpected layout or unpinned payload'
 for name,sha,size,crc in rows:
  b=body['WINXT/'+name]
  assert (len(b),hashlib.sha256(b).hexdigest(),zlib.crc32(b))==(int(size),sha,int(crc,16)),name
 for n in ('CUBE.EXE','STARFLD.EXE','MATRIX.EXE','ORBITS.EXE','TANDY88.DRV','TNDY6404.DRV','TNDY3204.DRV','TNDY160.DRV','TNDY6402.DRV'):
  assert body['WINXT/'+n][:2]==b'MZ',n
 assert not any('MAZE' in n.upper() for n in body)
 for n in ('TSHELL.INI','APPS.TXT'):assert b'MAZE' not in body['WINXT/'+n].upper()
 ini=body['WINXT/TSHELL.INI']
 assert b'IdleSeconds=300\r\n' in ini and b'OvalsProgram=C:\\WINXT\\ORBITS.EXE' in ini
 oem=body['WINXT/OEMSETUP.INF']
 for n in ('TANDY88.DRV','TNDY6404.DRV','TNDY3204.DRV','TNDY160.DRV','TNDY6402.DRV'):assert n.encode() in oem
 assert b'/320' in body['README.TXT'] or b'MODEXT' in body['README.TXT']
 print('PASS:',len(body),'members; all native pins, exact archive, quartet, five modes, layout and idle seed')
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--archive',type=Path,default=HERE/'BIN/WINXT.ZIP');p.add_argument('--native',type=Path,default=HERE/'NATIVE');a=p.parse_args();check(a.archive,a.native)
