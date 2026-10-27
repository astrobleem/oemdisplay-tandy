"""Negative coverage/lifecycle checks using real native receipt metadata."""
from pathlib import Path
import argparse,importlib.machinery,json,re,tempfile,unittest
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
M=importlib.machinery.SourceFileLoader('dib_repeat_gate_under_test',str(HERE/'CHECKREP.PY')).load_module()
class Gate(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(prefix='hpdib-gate-');self.out=Path(self.tmp.name)
  for n in ('PANQA.LOG','RESULT.JSN','LEASE.JSN','PREPARE.JSN'):(self.out/n).write_bytes((self.fixture/n).read_bytes())
 def tearDown(self):self.tmp.cleanup()
 def change(self,name,key,value):
  p=self.out/name;r=json.loads(p.read_text());r[key]=value;p.write_text(json.dumps(r))
 def log(self,fn):
  p=self.out/'PANQA.LOG';p.write_text(fn(p.read_text()))
 def reject(self):
  with patch.object(M.O,'verify',side_effect=AssertionError('Raster oracle must not run after failed preflight')):r=M.verify(self.out)
  self.assertEqual(r['status'],'FAIL');self.assertTrue(r['evidence_errors']);self.assertEqual(json.loads((self.out/'VERIFIED.JSN').read_text())['status'],'FAIL')
 def test_native_metadata_positive_control(self):
  self.assertEqual(M.preflight(self.out,(self.out/'PANQA.LOG').read_text())['status'],'PREFLIGHT_PASS')
 def test_zero_frames(self):self.log(lambda s:re.sub(r'^FRAME .*\n?','',s,flags=re.M));self.reject()
 def test_one_missing_frame(self):self.log(lambda s:re.sub(r'^FRAME id=12 .*\n?','',s,flags=re.M));self.reject()
 def test_duplicate_frame(self):self.log(lambda s:s+next(x for x in s.splitlines() if x.startswith('FRAME '))+'\n');self.reject()
 def test_wrong_frame_id(self):self.log(lambda s:s.replace('FRAME id=0 ','FRAME id=99 ',1));self.reject()
 def test_failed_dos_return(self):self.change('RESULT.JSN','normal_dos_return',False);self.reject()
 def test_incomplete_run(self):self.change('RESULT.JSN','complete',False);self.reject()
 def test_owned_emulator_not_stopped(self):self.change('RESULT.JSN','owned_stopped',False);self.reject()
 def test_error_even_when_complete(self):self.change('RESULT.JSN','error','timeout');self.reject()
 def test_lease_not_released(self):self.change('LEASE.JSN','lease_released',False);self.reject()
 def test_lease_failed(self):self.change('LEASE.JSN','status','FAILED');self.reject()
 def test_inventory_not_empty(self):self.change('LEASE.JSN','inventory_after',[{'pid':123}]);self.reject()
 def test_child_not_stopped(self):self.change('LEASE.JSN','children',[{'pid':123,'stopped':False}]);self.reject()
 def test_missing_child(self):self.change('LEASE.JSN','children',[]);self.reject()
 def test_missing_receipt(self):(self.out/'LEASE.JSN').unlink();self.reject()
 def test_non_object_receipt(self):(self.out/'RESULT.JSN').write_text('[]');self.reject()
 def test_wrong_installed_driver(self):self.change('RESULT.JSN','installed_driver',{'bytes':1,'sha256':'0'*64});self.reject()
 def test_review_reproduction(self):
  self.log(lambda s:re.sub(r'^FRAME .*\n?','',s,flags=re.M));self.change('RESULT.JSN','normal_dos_return',False);self.reject()
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--fixture',type=Path,required=True);v=a.parse_args();Gate.fixture=v.fixture;unittest.main(argv=['TESTGATE.PY'])
