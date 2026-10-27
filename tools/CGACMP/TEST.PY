"""Check preservation and refusal boundaries without claiming native coverage."""
from pathlib import Path
import argparse,importlib.machinery,json
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
 result=dict(outcome='PASS_HOST_COMPACT_PUBLICATION_GUARDS',checks=checks,native='NOT_EXERCISED',review='NOT_PROVIDED_BY_THIS_TEST')
 (a.out/'RESULT.JSN').write_text(json.dumps(result,indent=2)+'\n',encoding='ascii')
 print(json.dumps(result,indent=2))

if __name__=='__main__':main()
