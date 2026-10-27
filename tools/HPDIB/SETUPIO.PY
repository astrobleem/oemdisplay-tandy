"""Send bounded physical keyboard input only to this fixture's owned UI runner."""
from pathlib import Path
import argparse,json,time,collections,sys
sys.stdout.reconfigure(errors='backslashreplace')
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--text',default='');ap.add_argument('--taps',default='');ap.add_argument('--seconds',type=int,default=90);v=ap.parse_args();out=v.out.resolve();c=out/'CROOT'
assert 1<=v.seconds<=120
if v.text or v.taps:
 lease=json.loads((out/'FINAL-LEASE.JSON').read_text());assert lease['status']=='RUNNING' and lease['lease_acquired'] and lease['children'] and not any(x.get('stopped') for x in lease['children'])
 ack=json.loads((c/'RAWACK.JSON').read_text())['id'] if (c/'RAWACK.JSON').exists() else 0
 if (c/'RAWKEYS.JSON').exists():assert json.loads((c/'RAWKEYS.JSON').read_text())['id']<=ack,'Previous raw request still pending'
 taps=[int(n) for n in v.taps.split(',') if n];assert len(taps)<=32 and all(0<n<128 for n in taps)
 assert v.text.isascii() and len(v.text)<=128
 req={'id':ack+1,'text':v.text,'taps':taps};p=c/'RAWKEYS.NEW';p.write_text(json.dumps(req));p.replace(c/'RAWKEYS.JSON')
 end=time.monotonic()+v.seconds
 while time.monotonic()<end:
  if (c/'RAWACK.JSON').exists() and json.loads((c/'RAWACK.JSON').read_text())['id']==req['id']:break
  time.sleep(.2)
 else:raise TimeoutError('Owned Setup input acknowledgement')
text=(out/'DOS-CURRENT.TXT').read_text(encoding='utf-8',errors='replace') if (out/'DOS-CURRENT.TXT').exists() else ''
raw=(out/'DOS-RAW.BIN').read_bytes() if (out/'DOS-RAW.BIN').exists() else b''
for y in range(25):
 line=text[y*80:(y+1)*80].rstrip()
 if line.strip():print('%02d'%y,line,'attrs='+str(collections.Counter(raw[y*160+1:(y+1)*160:2]).most_common(3)) if raw else '')
