from pathlib import Path
import json,re,hashlib,struct
root=Path(__file__).resolve().parent;p=root/'runtime-tr51616-bltprof'
log=(p/'BLTPROF.LOG').read_text();r=json.loads((p/'RESULT.JSON').read_text())
samples=re.findall(r'^SAMPLE .*errors=0$',log,re.M);assert len(samples)==30
assert 'DONE errors=0' in log and 'CLEAN stopped' in log
assert len(re.findall(r'^READBACK ',log,re.M))==2
assert (p/'CUBEDONE.TXT').read_text().strip()=='RETURNED'
assert r['owned_stopped']and r['lease_released']and r['fat_copies_equal']
expected=json.loads((root/'tr5-input/IDENTITY.JSON').read_text());assert r['guest_driver_after']==dict(bytes=expected['bytes'],sha256=expected['sha256'])
out=dict(status='PASS',scope='Independent closed-file verification of completed native probe; original failed harness receipt retained',reason='Runner CRLF-sensitive regex counted zero valid records; parser repaired without rerunning or altering timing data',native_samples=len(samples),native_errors=0,owned_stopped=r['owned_stopped'],lease_released=r['lease_released'],fat_copies_equal=r['fat_copies_equal'],driver=r['guest_driver_after'],native_log_sha256=hashlib.sha256((p/'BLTPROF.LOG').read_bytes()).hexdigest())
(p/'CLOSED-VERIFY.JSON').write_text(json.dumps(out,indent=2));print(json.dumps(out))
