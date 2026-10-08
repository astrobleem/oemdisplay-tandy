"""Host contracts for pinned wave packaging/private own-media builder."""
import importlib.machinery, importlib.util, json, tempfile, unittest
import re
from pathlib import Path
HERE = Path(__file__).resolve().parent
def load(name,path):
    loader=importlib.machinery.SourceFileLoader(name,str(path));spec=importlib.util.spec_from_loader(name,loader)
    mod=importlib.util.module_from_spec(spec);loader.exec_module(mod);return mod
pkg=load('wave_package',HERE/'MAKEIMG.PY')
wave=HERE.parents[1]/'examples/WXTSPL/WAVE'
builder=load('wave_builder',wave/'MKSTART.PY')

def run_starter(text, reserve_status, wrapper_status):
    """Evaluate the generated DOS control flow with process return statuses.
    GOTO/ECHO leave ERRORLEVEL intact; no guest/hardware acceptance is inferred.
    """
    lines=text.splitlines();labels={s[1:]:i for i,s in enumerate(lines) if s.startswith(':')}
    pc=0;status=0;messages=[];called=[];directory='ROOT'
    for _ in range(100):
        if pc==len(lines):return status,messages,called,directory
        line=lines[pc];pc+=1
        if line.startswith(':') or line=='@ECHO OFF' or line.startswith('SET '):continue
        match=re.fullmatch(r'IF ERRORLEVEL (\d+) GOTO (\w+)',line)
        if match:
            if status>=int(match[1]):pc=labels[match[2]]
            continue
        if line.startswith('GOTO '):pc=labels[line[5:]];continue
        if line.startswith('ECHO '):messages.append(line[5:]);continue
        if line.startswith('CD '):directory=line[3:];continue
        if line=='RESERVE':status=reserve_status;called.append(line);continue
        if line=='XTCLEAN':status=wrapper_status;called.append(line);continue
        raise AssertionError('Unknown generated command: '+line)
    raise AssertionError('Generated starter did not terminate')

class WaveTest(unittest.TestCase):
    def test_starter_success_refusal_and_error_status_flow(self):
        text=builder.starter_batch()
        status,messages,calls,directory=run_starter(text,0,0)
        self.assertEqual((status,calls,directory),(0,['RESERVE','XTCLEAN'],'\\'))
        self.assertEqual(messages,['Windows returned.'])
        for code in (1,0xf1,0xf2,0xf3,0xff):
            with self.subTest(wrapper_status=code):
                status,messages,calls,directory=run_starter(text,0,code)
                self.assertEqual((status,calls,directory),(code,['RESERVE','XTCLEAN'],'WINDOWS'))
                self.assertEqual(messages,['Windows startup or cleanup failed; see WRAP.BIN.'])
        status,messages,calls,directory=run_starter(text,1,0)
        self.assertEqual((status,calls),(1,['RESERVE']))
        self.assertEqual(messages,['RESERVE refused; Windows was not started.'])
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
