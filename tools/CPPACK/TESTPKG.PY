"""Check the one-member overlay and refuse unqualified base/driver changes."""
from pathlib import Path
import importlib.machinery,json,tempfile,unittest
from unittest import mock
M=importlib.machinery.SourceFileLoader('cpp_overlay_test',str(Path(__file__).with_name('PACKAGE.PY'))).load_module()

class Overlay(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.old={'PCP3216.DRV':b'original fixed','PANCFG.EXE':b'qualified UI','INSTALL.TXT':b'current guide'}
        self.base=M.P.stored(self.old);self.fixed=b'native qualified fixed'
        folder=self.root/'tools/CPPACK';(folder/'PAYLOAD').mkdir(parents=True)
        (folder/'PAYLOAD/PCP3216.DRV').write_bytes(self.fixed)
        self.q={'complete':True,'driver':M.identity(self.fixed),'panning_reference':{'packet':M.identity(self.base)}}
    def outputs(self,q=None,base=None):
        (self.root/'tools/CPPACK/QUALIFY.JSN').write_text(json.dumps(q or self.q))
        with mock.patch.object(M,'ROOT',self.root),mock.patch.object(M.P,'outputs',return_value={'CPPAN.ZIP':self.base if base is None else base}):return M.outputs()
    def test_exactly_one_member_changes(self):
        out=self.outputs();files=M.members(out['CPPAN.ZIP'])
        self.assertEqual({n for n in files if files[n]!=self.old[n]},{'PCP3216.DRV'})
        self.assertEqual(out['INSTALL.TXT'],self.old['INSTALL.TXT'])
    def test_changed_live_panning_base_refused(self):
        with self.assertRaisesRegex(ValueError,'panning base changed'):
            self.outputs(base=M.P.stored(dict(self.old,**{'PANCFG.EXE':b'other UI'})))
    def test_wrong_fixed_driver_refused(self):
        (self.root/'tools/CPPACK/PAYLOAD/PCP3216.DRV').write_bytes(b'wrong')
        with self.assertRaisesRegex(ValueError,'Unqualified fixed'):self.outputs()
    def test_incomplete_qualification_refused(self):
        with self.assertRaisesRegex(ValueError,'Unqualified fixed'):self.outputs(dict(self.q,complete=False))
    def test_missing_fixed_member_cannot_expand_inventory(self):
        base=M.P.stored({n:b for n,b in self.old.items() if n!='PCP3216.DRV'})
        q=dict(self.q,panning_reference={'packet':M.identity(base)})
        with self.assertRaisesRegex(ValueError,'panning/installer/support'):self.outputs(q,base)

if __name__=='__main__':unittest.main()
