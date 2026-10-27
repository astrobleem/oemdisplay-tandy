"""Reject mismatched native inputs and unrelated packet changes before acceptance."""
from pathlib import Path
import argparse,copy,importlib.machinery,json,unittest
HERE=Path(__file__).resolve().parent
M=importlib.machinery.SourceFileLoader('dib_preparation_under_test',str(HERE/'PREPARE.PY')).load_module()
class Boundaries(unittest.TestCase):
 def test_real_native_driver_and_budget(self):self.assertEqual(M.validate_driver(self.driver,self.build),127133)
 def test_changed_driver_rejected(self):
  b=bytearray(self.driver);b[4096]^=1
  with self.assertRaisesRegex(ValueError,'binding'):M.validate_driver(bytes(b),self.build)
 def test_unreviewed_presentation_rejected(self):
  b=copy.deepcopy(self.build);b['presentation']='solid predicate'
  with self.assertRaisesRegex(ValueError,'presentation'):M.validate_driver(self.driver,b)
 def test_different_source_rejected(self):
  b=copy.deepcopy(self.build);b['dib_overlay_sha256']='0'*64
  with self.assertRaisesRegex(ValueError,'source/build'):M.validate_driver(self.driver,b)
 def test_restamped_budget_rejected(self):
  b=copy.deepcopy(self.build);b['gross_NE_bytes']+=1
  with self.assertRaisesRegex(ValueError,'budget'):M.validate_driver(self.driver,b)
 def test_payload_changes_exactly_three_members(self):
  before={'SETUP.EXE':b'old setup','WINXT/FIXXT.EXE':b'old fix','WINXT/HPXY.DRV':b'old driver','WINXT/PAN.EXE':b'accepted pan'}
  after=M.compose(before,b'new driver',b'new fix',b'new setup')
  self.assertEqual(after['WINXT/PAN.EXE'],before['WINXT/PAN.EXE']);self.assertEqual(set(after),set(before))
  with self.assertRaisesRegex(ValueError,'Unexpected'):M.compose(before,b'old driver',b'new fix',b'new setup')
 def test_consumer_python_refused(self):
  before={'SETUP.EXE':b'a','WINXT/FIXXT.EXE':b'b','WINXT/HPXY.DRV':b'c','WINXT/BUILD.PY':b'forbidden'}
  with self.assertRaisesRegex(ValueError,'Consumer'):M.compose(before,b'd',b'e',b'f')
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--driver',type=Path,required=True);a.add_argument('--build',type=Path,required=True);v=a.parse_args()
 Boundaries.driver=v.driver.read_bytes();Boundaries.build=json.loads(v.build.read_bytes());unittest.main(argv=['TESTPREP.PY'])
