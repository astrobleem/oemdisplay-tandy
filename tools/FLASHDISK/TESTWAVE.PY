"""Host contracts for pinned wave packaging/private own-media builder."""
import importlib.machinery, importlib.util, json, tempfile, unittest
from pathlib import Path
HERE = Path(__file__).resolve().parent
def load(name,path):
    loader=importlib.machinery.SourceFileLoader(name,str(path));spec=importlib.util.spec_from_loader(name,loader)
    mod=importlib.util.module_from_spec(spec);loader.exec_module(mod);return mod
pkg=load('wave_package',HERE/'MAKEIMG.PY')
wave=HERE.parents[1]/'examples/WXTSPL/WAVE'
builder=load('wave_builder',wave/'MKSTART.PY')
class WaveTest(unittest.TestCase):
    def test_exact_qualified_binary_and_public_allowlist(self):
        data=pkg.wave_payload()
        self.assertEqual(len(data),12)
        self.assertEqual(len(data['WAVE/XTLOGO.LGO']),35971)
        self.assertFalse(any('WIN.CNF' in n or 'XTTEST' in n for n in data))
        self.assertEqual(data['WAVE/XTLOGO.LGO'][:4],b'LOGO')
    def test_missing_wrong_loader_and_existing_output_refused(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);owned=root/'owned';(owned/'SYSTEM').mkdir(parents=True)
            (owned/'SYSTEM/WIN.CNF').write_bytes(b'wrong owned loader')
            with self.assertRaisesRegex(ValueError,'Unsupported owned'):builder.make(owned,root/'out')
            self.assertFalse((root/'out').exists())
            (root/'out').mkdir();(root/'out/USER.TXT').write_bytes(b'preserved')
            with self.assertRaisesRegex(ValueError,'existing files'):builder.make(owned,root/'out')
            self.assertEqual((root/'out/USER.TXT').read_bytes(),b'preserved')
if __name__=='__main__':unittest.main()
