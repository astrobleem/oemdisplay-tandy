"""Refuse concurrent helper rollback; no network or release mutations."""
from pathlib import Path
import importlib.machinery,json,tempfile,unittest
from unittest import mock
M=importlib.machinery.SourceFileLoader('cpp_scope_pub',str(Path(__file__).with_name('CPPUB.PY'))).load_module()

class Scope(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.out=self.root/'current';self.out.mkdir()
        self.files={'PCP3216.DRV':b'qualified fixed','PANCFG.EXE':b'new settings','INSTALL.TXT':b'current guide'}
        self.archive=M.P.archive(self.files)
        (self.root/'kit').write_bytes(self.archive);(self.root/'guide').write_bytes(self.files['INSTALL.TXT'])
        (self.out/'CPPAN.ZIP').write_bytes(self.archive);(self.out/'KEEP.ZIP').write_bytes(b'unrelated')
        pins={p.name:M.P.identity(p.read_bytes()) for p in self.out.iterdir()}
        (self.out/'CURRENT.JSN').write_bytes(M.P.text(json.dumps({'assets':pins})))
        (self.out/'CURRENT.SHA').write_bytes(M.P.text(''.join(M.P.identity(p.read_bytes())['sha256']+'  '+p.name+'\n' for p in sorted(self.out.iterdir()) if p.name!='CURRENT.SHA')))
        self.spec={'core_identities':{},'local':{'CPPAN.ZIP':{'source':'kit'}},'documentation_overlays':{'CPPAN.ZIP':{'member':'INSTALL.TXT','source':'guide'}}}
    def check(self,previous=None,damage_metadata=False,missing=False):
        previous=dict(self.files,**{'PCP3216.DRV':b'old fixed'}) if previous is None else previous
        data=M.P.archive(previous)
        rows=[]
        for p in self.out.iterdir():
            if missing and p.name=='CPPAN.ZIP':continue
            b=data if p.name=='CPPAN.ZIP' else p.read_bytes();pin=M.P.identity(b)
            rows.append({'name':p.name,'size':pin['bytes'],'digest':'sha256:'+pin['sha256'],'browser_download_url':'https://example.invalid/'+p.name})
        if damage_metadata:next(r for r in rows if r['name']=='CPPAN.ZIP')['size']+=1
        release={'tag_name':'windows-xt','draft':False,'immutable':False,'assets':rows}
        with mock.patch.object(M,'ROOT',self.root),mock.patch.object(M.P,'spec',return_value=self.spec),mock.patch.object(M.V,'verify',return_value=({'driver':M.P.identity(self.files['PCP3216.DRV'])},{})),mock.patch.object(M,'download',return_value=data):
            return M.check(self.out,release)
    def test_only_fixed_driver_change(self):self.check()
    def test_newer_live_settings_cannot_be_rolled_back(self):
        with self.assertRaisesRegex(ValueError,'panning/installer/support'):
            self.check(dict(self.files,**{'PANCFG.EXE':b'newer settings'}))
    def test_live_member_closure_preserved(self):
        with self.assertRaisesRegex(ValueError,'panning/installer/support'):
            self.check(dict(self.files,**{'USER.TXT':b'new official member'}))
    def test_anonymous_download_must_match_metadata(self):
        with self.assertRaisesRegex(ValueError,'release metadata'):self.check(damage_metadata=True)
    def test_already_uploaded_packet_can_finish_catalog(self):self.check(dict(self.files))
    def test_interrupted_missing_allowlisted_packet_can_be_repaired(self):self.check(missing=True)

if __name__=='__main__':unittest.main()
