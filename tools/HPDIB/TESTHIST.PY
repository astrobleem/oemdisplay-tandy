"""Historical replay preserves exact pins and refuses unrelated source changes."""
from pathlib import Path
import hashlib,importlib.machinery,io,json,unittest,zipfile
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
H=importlib.machinery.SourceFileLoader('hpdib_history_test',str(HERE/'HISTORY.PY')).load_module()
class Historical(unittest.TestCase):
 def setUp(self):self.pins=json.loads((H.ROOT/'tools/PAN/ACCEPT.JSN').read_bytes())['sources']
 def test_all_preserved_sources(self):
  for n in H.NAMES:
   b=H.previous_source(n,self.pins[n]);self.assertEqual({'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()},self.pins[n])
 def test_wrong_pin(self):
  with self.assertRaises(ValueError):H.previous_source(H.NAMES[0],dict(bytes=0,sha256='0'*64))
 def test_unrelated_changed_source(self):
  with self.assertRaisesRegex(ValueError,'outside snapshot'):H.previous_source('tools/HPDIB/README.MD',dict(bytes=0,sha256='0'*64))
 def test_corrupt_archive(self):
  old=Path.read_bytes;snapshot=HERE/'BASE/SRCPAN.ZIP'
  with patch.object(Path,'read_bytes',lambda p:b'corrupt' if p==snapshot else old(p)):
   with self.assertRaisesRegex(ValueError,'source snapshot'):H.previous_source(H.NAMES[0],self.pins[H.NAMES[0]])
 def test_extra_member_rejected(self):
  old=Path.read_bytes;snapshot=HERE/'BASE/SRCPAN.ZIP';buf=io.BytesIO()
  with zipfile.ZipFile(snapshot) as src,zipfile.ZipFile(buf,'w') as dst:
   for n in src.namelist():dst.writestr(n,src.read(n))
   dst.writestr('EXTRA.TXT',b'unexpected')
  raw=buf.getvalue()
  with patch.object(H,'SHA',hashlib.sha256(raw).hexdigest()),patch.object(Path,'read_bytes',lambda p:raw if p==snapshot else old(p)):
   with self.assertRaisesRegex(ValueError,'inventory'):H.previous_source(H.NAMES[0],self.pins[H.NAMES[0]])
if __name__=='__main__':unittest.main()
