"""Check preservation and refusal boundaries without claiming native coverage."""
from pathlib import Path
import argparse,copy,importlib.machinery,json
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
P=importlib.machinery.SourceFileLoader('compact_prior_gate_test',str(ROOT/'tools/PAN/PUBLISH.PY')).load_module()
V=importlib.machinery.SourceFileLoader('compact_gate_test',str(HERE/'VERIFY.PY')).load_module()

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
 a.out.mkdir(parents=True,exist_ok=False);checks=[]
 q,packets=P.products()
 assert {n:P.identity(b) for n,b in packets.items()}==q['packets']
 assert P.verify_alternatives(packets)['CGA.ZIP']==q['packets']['CGA.ZIP']
 checks.append('All five preceding packets and their exact payload inventories preserved')
 for n in P.H.NAMES:assert P.identity(P.H.previous_source(n,q['sources'][n]))==q['sources'][n]
 checks.append('Eight superseded sources recover only original exact accepted identities')
 try:P.H.previous_source('src/cga/CGASET.PY',dict(bytes=0,sha256='0'*64))
 except ValueError as e:assert 'outside snapshot' in str(e)
 else:raise AssertionError('Unarchived changed source accepted')
 checks.append('Changed source outside closed historical snapshot refused')
 previous=V.HERE
 try:
  V.HERE=a.out/'missing';V.HERE.mkdir()
  try:V.verify()
  except ValueError as e:assert 'acceptance pending' in str(e)
  else:raise AssertionError('Missing native/review acceptance allowed')
  checks.append('Missing compact native/review acceptance refused')
  V.HERE=a.out/'pending';V.HERE.mkdir();(V.HERE/'ACCEPT.JSN').write_text(json.dumps(dict(status='PENDING',physical_hardware=False)))
  try:V.verify()
  except ValueError as e:assert 'acceptance pending' in str(e)
  else:raise AssertionError('Pending native/review acceptance allowed')
  checks.append('Pending acceptance refused before packet assembly')
  (V.HERE/'ACCEPT.JSN').write_text(json.dumps(dict(status='REVIEWED_NATIVE_COMPACT_CGA',physical_hardware=False,runtime_source='a'*40,sources={})))
  try:V.verify()
  except ValueError as e:assert 'source binding incomplete' in str(e)
  else:raise AssertionError('Empty reviewed source declaration allowed')
  checks.append('Reviewed label cannot replace complete compact source bindings')
 finally:V.HERE=previous
 # An alternate CGA packet must enter the new gate; legacy acceptance alone
 # cannot qualify a new ZIP even if all other consumer packets are exact.
 bad=dict(packets);bad['CGA.ZIP']=b'unqualified compact packet'
 try:P.verify_alternatives(bad)
 except (ValueError,FileNotFoundError):pass
 else:raise AssertionError('Unqualified alternate CGA packet accepted')
 checks.append('Current alternative boundary rejects unqualified compact packet')
 pending=ROOT/'docs/QUAL/CGACMP/CANDIDATE.JSN'
 if pending.exists():
  native=json.loads(pending.read_bytes());V.validate_candidate(native)
  checks.append('Exact completed native candidate validates without accepting review/publication')
  def refuses_bad(candidate,needle,substitutions=None):
   old=V.exact
   def exact(row):
    if substitutions and row['path'] in substitutions:
     raw=substitutions[row['path']];assert V.identity(raw)==row['identity'];return raw
    return old(row)
   V.exact=exact
   try:
    try:V.validate_candidate(candidate)
    except ValueError as e:assert needle in str(e),str(e)
    else:raise AssertionError('Incomplete native candidate accepted')
   finally:V.exact=old
  bad=copy.deepcopy(native);bad['windows'].pop('640C');refuses_bad(bad,'Both compact Windows')
  checks.append('Missing second native Windows profile refused')
  bad=copy.deepcopy(native);bad['windows']['320C']['result']=native['windows']['640C']['result'];refuses_bad(bad,'application coverage incomplete')
  checks.append('Other-resolution application receipt cannot substitute for320C')
  bad=copy.deepcopy(native);result=json.loads(V.exact(bad['windows']['640C']['result']));result['machine']['mem_size']='1024';raw=json.dumps(result).encode()
  bad['windows']['640C']['result']=dict(path='TEST-WRONG-RAM',identity=V.identity(raw));refuses_bad(bad,'Native IBM XT/CGA fixture differs',{'TEST-WRONG-RAM':raw})
  checks.append('A larger-RAM native declaration cannot qualify normal640KB')
  # Reproduce the review finding: change actual config bytes and refresh all
  # identities, keeping the plausible XT/640KB declaration untouched.
  for label,old,new in [
   ('386 with1MB','cpu_family = 8088\r\n','cpu_family = 386\r\nmem_size = 1024\r\n'),
   ('largerRAM','mem_size = 640','mem_size = 1024'),
   ('otherCPU','cpu_family = 8088','cpu_family = 386'),
   ('otherclock','cpu_speed = 4772728','cpu_speed = 8000000'),
   ('othermachine','machine = ibmxt86','machine = ibmat'),
   ('othergraphics','gfxcard = cga','gfxcard = vga'),
   ('dynarec','cpu_use_dynarec = 0','cpu_use_dynarec = 1'),
   ('CPUmultiplier','cpu_multi = 1','cpu_multi = 2'),
   ('memoryoverride','mem_size = 640','mem_size = 640\r\nmem_size_ext = 1024'),
   ('memoryboard','[Video]','[ISA memory expansion #1]\r\nsize = 2048\r\n\r\n[Video]'),
   ('defaults','[General]','[DEFAULT]\r\ncpu_use_dynarec = 1\r\n\r\n[General]'),
   ('duplicateoption','mem_size = 640','mem_size = 640\r\nmem_size = 1024')]:
   bad=copy.deepcopy(native);row=bad['windows']['640C'];raw=V.exact(row['config']);assert old.encode() in raw
   changed=raw.replace(old.encode(),new.encode())
   if label=='386 with1MB':changed=changed.replace(b'mem_size = 640\r\n',b'')
   result=json.loads(V.exact(row['result']));result['config']=V.identity(changed);raw_result=json.dumps(result).encode()
   row['config']=dict(path='TEST-CONFIG',identity=V.identity(changed));row['result']=dict(path='TEST-RESULT',identity=V.identity(raw_result))
   refuses_bad(bad,'Native IBM XT/CGA configuration',{'TEST-CONFIG':changed,'TEST-RESULT':raw_result})
   checks.append('Restamped actual configuration refused with unchanged declaration: '+label)
  bad=copy.deepcopy(native);lease=json.loads(V.exact(bad['windows']['320C']['lease']));lease['status']='FAILED';raw=json.dumps(lease).encode()
  bad['windows']['320C']['lease']=dict(path='TEST-FAILED-RUN',identity=V.identity(raw));refuses_bad(bad,'cleanup incomplete',{'TEST-FAILED-RUN':raw})
  checks.append('A retained failed run cannot qualify a Windows profile')
 result=dict(outcome='PASS_HOST_COMPACT_PUBLICATION_GUARDS',checks=checks,native='RECORDED_EVIDENCE_CHECKED' if pending.exists() else 'NOT_EXERCISED',review='NOT_PROVIDED_BY_THIS_TEST')
 (a.out/'RESULT.JSN').write_text(json.dumps(result,indent=2)+'\n',encoding='ascii')
 print(json.dumps(result,indent=2))

if __name__=='__main__':main()
