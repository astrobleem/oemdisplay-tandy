from pathlib import Path
import json,re,hashlib,statistics
from PIL import Image,ImageChops
root=Path(__file__).resolve().parent
def pin(p):
 b=p.read_bytes();return dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
report=dict(driver=json.loads((root/'tr5-input/IDENTITY.JSON').read_text()),comparison={},pixels={})
for variant in ('control','selected'):
 p=root/('runtime-tr51616-'+variant);result=json.loads((p/'RESULT.JSON').read_text());assert result['status']=='PASS'
 rows=[]
 for block in (p/'CUBE.LOG').read_text().split('START ')[1:]:
  m=re.search(r'END reason=(\S+) frames=(\d+) errors=(\d+) draw_ms=(\d+)',block);assert m and m[2]=='13' and m[3]=='0'
  rows.append(dict(style=int(re.search(r' style=(\d+)',block)[1]),frames=int(m[2]),draw_ms=int(m[4])))
 assert len(rows)==6
 report['comparison'][variant]=dict(process=result,preparation=json.loads((p/'PREPARE.JSON').read_text()),cases=rows,mean_ms={str(s):sum(r['draw_ms']for r in rows if r['style']==s)/26 for s in (1,2,3)})
a=root/'runtime-tr51616-control';b=root/'runtime-tr51616-selected'
for p in a.glob('STYLE*.PNG'):
 q=b/p.name;equal=ImageChops.difference(Image.open(p).convert('RGB'),Image.open(q).convert('RGB')).getbbox()is None
 report['pixels'][p.name]=dict(equal=equal,control=pin(p),selected=pin(q));assert equal
assert len(report['pixels'])==12
c=report['comparison']['control']['mean_ms'];s=report['comparison']['selected']['mean_ms'];report['reduction_percent']={k:100*(1-s[k]/c[k])for k in c}
probe=root/'runtime-tr51616-bltprof';verify=json.loads((probe/'CLOSED-VERIFY.JSON').read_text());log=(probe/'BLTPROF.LOG').read_text()
report['probe']=dict(closed_verification=verify,original_result=json.loads((probe/'RESULT.JSON').read_text()),log=pin(probe/'BLTPROF.LOG'),records=log.splitlines())
(root/'TR51616-VALIDATION.JSON').write_text(json.dumps(report,indent=2)+'\n')
lines=['Current TR5 160x200 cube validation, 2026-10-30','Driver TR51616.DRV '+report['driver']['sha256']+' (54880 bytes, Git blob '+report['driver']['git_blob_sha']+').','This supersedes performance conclusions drawn from historical TNDY160.DRV. Historical records remain intact.','Private 86Box Tandy 1000 HX, 8088 7159092 Hz, dynarec disabled, 640 KB, RESERVE 32, Windows 3.0 WIN /R, XTC fonts. Identical control/selected EXEs and 13 phases39..135 step8; 26 frames/style. QA holds excluded; QA pixel readbacks included.']
for k,name in [('1','Flat'),('2','Dither'),('3','Wire')]:lines.append('%s control %.2f -> selected %.2f ms/frame (%.2f%% reduction)'%(name,c[k],s[k],report['reduction_percent'][k]))
lines+=['Both runs passed 78 frames, six source/screen readbacks and cleanup; all 12 paired full-screen captures are pixel-identical. No driver bytes changed.','Separate BitBlt probe: color memory full/dirty medians 22.3125/19.7422 ms per call; color display full/dirty116.75/96.125. Mono memory21.8828/18.8828; mono display116.625/89.25. Full49x95, dirty41x85, 3 batches each (128 memory or8 display calls).','Identity display full/1-pixel copies median549.25/528.625 ms/call are a documented full-resynchronization proxy. They do not represent ordinary cube bitmap-to-display calls. Memory/display differences include dispatch and conversion as well as flushing; internal flush-only cycles were not isolated. No driver change is proposed.','Probe completed30 error-free samples and native cleanup. Original host result FAIL retained: CRLF regex counted0 samples. Corrected parser plus independent closed-log/driver/FAT verification passed without rerunning or replacing measurements.','All owned children stopped and leases released; matched driver bytes verified after runtime. BOR/Mesen untouched. Physical hardware, full-period raster equality, other sizes/modes and full release-package qualification remain outside scope.']
(root/'TR51616-VALIDATION.TXT').write_text('\n\n'.join(lines)+'\n')
print(json.dumps(dict(control=c,selected=s,reduction=report['reduction_percent'],pixel_pairs=len(report['pixels'])),indent=2))
