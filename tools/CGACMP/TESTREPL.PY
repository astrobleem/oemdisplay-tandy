"""Host refusal checks for immutable pre-UI replay; no files or new receipts."""
from pathlib import Path
import hashlib,importlib.machinery as M,json,subprocess,unittest
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
R=M.SourceFileLoader('immutable_ui_test',str(HERE/'REPLAY.PY')).load_module()
H=M.SourceFileLoader('immutable_pan_test',str(HERE.parent/'HPDIB/HISTORY.PY')).load_module()
class Replay(unittest.TestCase):
 def setUp(self):self.pins=json.loads((HERE/'ACCEPT.JSN').read_bytes())['sources']
 def test_exact_original_sources_only(self):
  view=R.SourceView()
  for name in (*R.INPUTS,R.GATE):self.assertEqual(R.identity((view/name).read_bytes()),self.pins[name])
  self.assertEqual(view/'src/cga/CGAFONT.PY',R.ROOT/'src/cga/CGAFONT.PY')
 def test_wrong_pin_refused_for_every_exception(self):
  for name in (*R.INPUTS,R.GATE):
   with self.subTest(name=name),self.assertRaisesRegex(ValueError,'pin differs'):
    R.original(name,dict(bytes=0,sha256='0'*64))
 def test_unrelated_source_cannot_use_git_fallback(self):
  name='src/cga/CGAFONT.PY';raw=(R.ROOT/name).read_bytes()
  with self.assertRaisesRegex(ValueError,'outside immutable'):R.original(name,R.identity(raw))
 def test_missing_immutable_object_fails_closed_without_fetch(self):
  with patch.object(R.subprocess,'check_output',side_effect=subprocess.CalledProcessError(128,['git'])):
   with self.assertRaisesRegex(ValueError,'fetch exact revision '+R.REVISION):R.original(R.GATE,self.pins[R.GATE])
 def test_two_legacy_instruction_inputs_only(self):
  pins=json.loads((R.ROOT/'tools/CGAFRESH/ACCEPT.JSN').read_bytes())['sources']
  self.assertEqual(R.FRESH_INPUTS,{'docs/CGA.MD','src/cga/FRESH.TXT'})
  for name in R.FRESH_INPUTS:
   self.assertEqual(R.identity(R.original(name,pins[name])),pins[name])
   with self.assertRaisesRegex(ValueError,'pin differs'):R.original(name,dict(bytes=0,sha256='0'*64))
  with self.assertRaisesRegex(ValueError,'outside immutable'):R.original('src/cga/FRESH.C',pins['src/cga/FRESH.C'])
 def test_preceding_pan_pin_still_required(self):
  pin=json.loads((R.ROOT/'tools/PAN/ACCEPT.JSN').read_bytes())['sources']['src/cga/CGASET.PY']
  self.assertEqual(R.identity(H.previous_source('src/cga/CGASET.PY',pin)),pin)
  with self.assertRaisesRegex(ValueError,'pin differs'):H.previous_source('src/cga/CGASET.PY',dict(bytes=0,sha256='0'*64))
if __name__=='__main__':unittest.main()
