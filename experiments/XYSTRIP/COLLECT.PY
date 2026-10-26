"""Collect completed private build/Windows integration receipts, without running."""
from pathlib import Path
import csv,hashlib,json,re,struct
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
OUT=ROOT.parent/'tandy-pan-integration'
def ident(b):return dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
result=dict(status='PASS_FOCUSED_WINDOWS_EMULATOR',source_base='8d48aa04560a4730c9ee3d946bed865ca9be0c43',
            physical_hardware=False,publication=False,builds={},windows={},source={},gaps=[
                'Physical EX/8088 timing and visible blank interval not measured',
                'No new retrace scheduling or general prewrite split',
                'No helper repeat-step or chunking policy changes',
                'No installer/package acceptance or arbitrary-application coverage',
                'No deliberately exhausted-memory or natural retrace-timeout test'])
for name in ['baseline','candidate']:
    build=OUT/(name+'-build');driver=(build/'HPXY.DRV').read_bytes()
    r=json.loads((build/'RESULT.json').read_text());assert r['sha256']==ident(driver)['sha256']
    ne=struct.unpack_from('<I',driver,0x3c)[0]
    count=struct.unpack_from('<H',driver,ne+0x1c)[0];off=ne+struct.unpack_from('<H',driver,ne+0x22)[0]
    segments=[dict(index=i+1,file_bytes=struct.unpack_from('<H',driver,off+i*8+2)[0],
                   allocation=struct.unpack_from('<H',driver,off+i*8+6)[0] or 65536) for i in range(count)]
    result['builds'][name]=dict(receipt=r,identity=ident(driver),segments=segments)
    for tag in ['', '-qual']:
        folder=OUT/('windows-'+name+tag)
        q=json.loads((folder/'VERIFIED.JSN').read_text());assert q['status']=='PASS'
        execution=json.loads((folder/'RESULT.JSN').read_text());lease=json.loads((folder/'LEASE.JSN').read_text())
        assert execution['complete'] and execution['owned_stopped'] and execution['normal_dos_return']
        assert execution['bios_kb']==624 and execution['installed_driver']==ident(driver)
        assert lease['lease_acquired'] and lease['lease_released'] and lease['status']=='PASS'
        assert all(c['stopped'] for c in lease['children'])
        result['windows'][name+tag]=dict(verification=q,execution={k:v for k,v in execution.items() if k!='log'},
            lease=lease,prepared=json.loads((folder/'PREPARE.JSN').read_text()))
paths=['experiments/XYPAN/XYPAN.ASM','experiments/XYPAN/XYCOPY.ASM','experiments/XYPAN/XYPATCH.PY',
       'experiments/XYRRECT/XRBUILD.PY']
for path in paths:
    b=(ROOT/path).read_bytes();assert b==(OUT/'candidate-view'/path).read_bytes()
    result['source'][path]=ident(b)
result['gross_NE_delta']=result['builds']['candidate']['receipt']['gross_NE_bytes']-result['builds']['baseline']['receipt']['gross_NE_bytes']
result['ceiling_margin']=102955+24576-result['builds']['candidate']['receipt']['gross_NE_bytes']
result['total_verified_frames']=sum(x['verification']['frames'] for x in result['windows'].values())
result['total_compared_bytes']=sum(x['verification']['compared_bytes'] for x in result['windows'].values())
rows=[]
for tag in ['', '-qual']:
    a=result['windows']['baseline'+tag]['verification']['moves'];b=result['windows']['candidate'+tag]['verification']['moves']
    for x,y in zip(a,b):
        assert x['x']==y['x'] and x['y']==y['y']
        rows.append(dict(suite='original' if not tag else 'extended',id=x['id'],x=x['x'],y=x['y'],
                         baseline_ms=x['ms'],candidate_ms=y['ms'],baseline_bytes=x['bytes'],candidate_bytes=y['bytes'],
                         candidate_reason=y['reason']))
with (OUT/'MOVEMENTS.CSV').open('w',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
(OUT/'INTEGRATION.JSN').write_text(json.dumps(result,indent=2)+'\n')
(OUT/'CANDIDATE.SHA').write_text(result['builds']['candidate']['identity']['sha256']+'  candidate-build/HPXY.DRV\n')
print('PASS: receipt, driver identity, 624K BIOS layout, owned stop/release, source closure')
print('Frames',result['total_verified_frames'],'bytes',result['total_compared_bytes'])
for row in rows:print(row)
