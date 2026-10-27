"""Publication must refuse unqualified records and incomplete native cleanup."""
from pathlib import Path
import argparse,copy,importlib.machinery,json,tempfile,unittest
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
M=importlib.machinery.SourceFileLoader('dib_publication_under_test',str(HERE/'PUBLISH.PY')).load_module()
class Publication(unittest.TestCase):
 def test_real_clean_lease(self):M.clean(copy.deepcopy(self.lease))
 def test_incomplete_cleanup_rejected(self):
  for key,value in [('status','RUNNING'),('lease_acquired',False),('lease_released',False),('inventory_after',[{'pid':123}]),('children',[]),('children',[{'pid':123,'stopped':False}])]:
   q=copy.deepcopy(self.lease);q[key]=value
   with self.subTest(field=key),self.assertRaises(ValueError):M.clean(q)
 def test_preparation_cannot_publish(self):
  original=Path.read_bytes
  def read(p):return json.dumps({'status':'PREPARED_NOT_QUALIFIED','physical_hardware':False}).encode() if p==HERE/'ACCEPT.JSN' else original(p)
  with tempfile.TemporaryDirectory(prefix='hpdib-publish-test-') as t,patch.object(Path,'read_bytes',read):
   out=Path(t)/'output'
   with self.assertRaisesRegex(ValueError,'qualification pending'):M.build(out,'0'*40)
   self.assertFalse(out.exists())
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--lease',type=Path,required=True);v=a.parse_args();Publication.lease=json.loads(v.lease.read_text());unittest.main(argv=['TESTPUB.PY'])
