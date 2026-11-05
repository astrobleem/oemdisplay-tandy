"""Refuse helper/PC1 rollback and unqualified driver edits; no release writes."""
from pathlib import Path
import importlib.machinery,json,os,sys,tempfile,unittest
from unittest import mock
M=importlib.machinery.SourceFileLoader('cpp_scope_pub',str(Path(__file__).with_name('CPPUB.PY'))).load_module()

def yamaha(driver=b'qualified Yamaha',support=b'unchanged support'):
    files={'YAM160.DRV':driver,'CGA.GR2':support,'OEMSETUP.INF':b'unchanged selector'}
    record={'schema':1,'profile':'b800','driver':'YAM160.DRV','selector':'unchanged label',
            'files':{n:M.P.identity(b) for n,b in sorted(files.items())},
            'external_support_inputs':[],'native_test':'not asserted by host packaging'}
    files['MANIFEST.JSN']=M.P.text(json.dumps(record,indent=2,sort_keys=True)+'\n')
    files['SHA256.SUM']=M.P.text(''.join(M.P.identity(b)['sha256']+'  '+n+'\n' for n,b in sorted(files.items())))
    return files

class Scope(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.out=self.root/'current';self.out.mkdir()
        self.files={'PCP3216.DRV':b'qualified fixed','PANCFG.EXE':b'new settings','INSTALL.TXT':b'current guide'}
        self.yamaha=yamaha()
        self.archive=M.P.archive(self.files);self.yamarchive=M.P.archive(self.yamaha)
        (self.root/'kit').write_bytes(self.archive);(self.root/'guide').write_bytes(self.files['INSTALL.TXT'])
        (self.root/'yamaha').write_bytes(self.yamarchive)
        (self.out/'CPPAN.ZIP').write_bytes(self.archive);(self.out/'YAMAHA.ZIP').write_bytes(self.yamarchive)
        (self.out/'PC1.ZIP').write_bytes(b'unchanged PC1');(self.out/'KEEP.ZIP').write_bytes(b'unrelated')
        self.catalog()
        self.spec={'core_identities':{},'local':{'CPPAN.ZIP':{'source':'kit'},
                   'YAMAHA.ZIP':{'source':'yamaha','identity':M.P.identity(self.yamarchive)},
                   'PC1.ZIP':{'identity':M.P.identity(b'unchanged PC1')}},
                   'documentation_overlays':{'CPPAN.ZIP':{'member':'INSTALL.TXT','source':'guide'}}}
    def catalog(self):
        pins={p.name:M.P.identity(p.read_bytes()) for p in self.out.iterdir() if p.name not in {'CURRENT.JSN','CURRENT.SHA'}}
        (self.out/'CURRENT.JSN').write_bytes(M.P.text(json.dumps({'assets':pins})))
        (self.out/'CURRENT.SHA').write_bytes(M.P.text(''.join(M.P.identity(p.read_bytes())['sha256']+'  '+p.name+'\n' for p in sorted(self.out.iterdir()) if p.name!='CURRENT.SHA')))
    def check(self,previous=None,previous_yamaha=None,damage_metadata=False,missing=(),live_overrides=None,extra_rows=(),qualification=None,yamaha_error=None):
        previous=dict(self.files,**{'PCP3216.DRV':b'old fixed'}) if previous is None else previous
        previous_yamaha=yamaha(b'old Yamaha') if previous_yamaha is None else previous_yamaha
        bodies={p.name:p.read_bytes() for p in self.out.iterdir()}
        bodies.update({'CPPAN.ZIP':M.P.archive(previous),'YAMAHA.ZIP':M.P.archive(previous_yamaha)})
        bodies.update(live_overrides or {})
        rows=[]
        for name,b in bodies.items():
            if name in missing:continue
            pin=M.P.identity(b)
            rows.append({'name':name,'size':pin['bytes'],'digest':'sha256:'+pin['sha256'],'browser_download_url':'https://example.invalid/'+name})
        rows.extend(extra_rows)
        if damage_metadata:next(r for r in rows if r['name']=='CPPAN.ZIP')['size']+=1
        release={'tag_name':'windows-xt','draft':False,'immutable':False,'assets':rows}
        qualified=qualification or {'driver':M.P.identity(self.files['PCP3216.DRV'])}
        with mock.patch.object(M,'ROOT',self.root),mock.patch.object(M.P,'spec',return_value=self.spec),mock.patch.object(M.V,'verify',return_value=(qualified,{})),mock.patch.object(M,'optimized_guide',side_effect=lambda original:b'approved optimized guide: '+original) as guide,mock.patch.object(M,'yamaha_verify',side_effect=yamaha_error) as gate,mock.patch.object(M,'download',side_effect=lambda url:bodies[url.rsplit('/',1)[1]]):
            result=M.check(self.out,release)
            gate.assert_called_once_with(self.yamarchive)
            if qualified.get('optimized'):guide.assert_called_once_with((self.root/'guide').read_bytes())
            else:guide.assert_not_called()
            return result
    def test_only_two_fixed_driver_changes(self):self.check()
    def test_exact_upload_allowlist(self):
        self.assertEqual(M.ORDER,('CPPAN.ZIP','YAMAHA.ZIP','CURRENT.SHA','CURRENT.JSN'))
    def test_noncanonical_candidate_packet_rejected(self):
        (self.out/'CPPAN.ZIP').write_bytes(self.archive+b'trailing bytes');self.catalog()
        with self.assertRaisesRegex(ValueError,'Noncanonical'):self.check()
    def test_noncanonical_live_packet_rejected(self):
        with self.assertRaisesRegex(ValueError,'Noncanonical'):
            self.check(live_overrides={'YAMAHA.ZIP':self.yamarchive+b'trailing bytes'})
    def test_newer_live_settings_cannot_be_rolled_back(self):
        with self.assertRaisesRegex(ValueError,'panning/installer/support'):
            self.check(dict(self.files,**{'PANCFG.EXE':b'newer settings'}))
    def optimized(self,guide=None):
        self.spec['documentation_overlays']['CPPAN.ZIP']['transform']='optimized-colorplus'
        files=dict(self.files,**{'INSTALL.TXT':b'approved optimized guide: '+self.files['INSTALL.TXT'] if guide is None else guide})
        (self.out/'CPPAN.ZIP').write_bytes(M.P.archive(files));self.catalog()
        return {'driver':M.P.identity(self.files['PCP3216.DRV']),'optimized':True}
    def test_exact_optimized_guide_is_allowed(self):
        self.check(qualification=self.optimized())
    def test_optimized_guide_only_update_is_allowed(self):
        self.check(previous=dict(self.files),qualification=self.optimized())
    def test_wrong_optimized_guide_is_blocked(self):
        with self.assertRaisesRegex(ValueError,'guide differs from qualified derivation'):
            self.check(qualification=self.optimized(b'arbitrary guide edit'))
    def test_raw_legacy_guide_is_blocked_for_optimized_driver(self):
        with self.assertRaisesRegex(ValueError,'guide differs from qualified derivation'):
            self.check(qualification=self.optimized(self.files['INSTALL.TXT']))
    def test_optimized_guide_does_not_allow_support_changes(self):
        qualification=self.optimized()
        with self.assertRaisesRegex(ValueError,'panning/installer/support'):
            self.check(previous=dict(self.files,**{'PANCFG.EXE':b'newer settings'}),qualification=qualification)
    def test_unknown_guide_transform_is_blocked(self):
        for optimized in (False,True):
            qualification=self.optimized() if optimized else None
            self.spec['documentation_overlays']['CPPAN.ZIP']['transform']='unrecognized'
            with self.subTest(optimized=optimized),self.assertRaisesRegex(ValueError,'guide transform'):
                self.check(qualification=qualification)
    def test_optimized_guide_requires_explicit_transform(self):
        qualification=self.optimized();del self.spec['documentation_overlays']['CPPAN.ZIP']['transform']
        with self.assertRaisesRegex(ValueError,'guide transform'):self.check(qualification=qualification)
    def test_legacy_qualification_cannot_authorize_transform(self):
        self.optimized()
        with self.assertRaisesRegex(ValueError,'guide transform'):self.check()
    def test_live_colorplus_member_closure_preserved(self):
        with self.assertRaisesRegex(ValueError,'panning/installer/support'):
            self.check(dict(self.files,**{'USER.TXT':b'new official member'}))
    def test_yamaha_support_cannot_change(self):
        with self.assertRaisesRegex(ValueError,'panning/installer/support'):
            self.check(previous_yamaha=yamaha(b'old Yamaha',b'newer support'))
    def test_yamaha_member_closure_preserved(self):
        with self.assertRaisesRegex(ValueError,'panning/installer/support'):
            self.check(previous_yamaha=dict(yamaha(b'old Yamaha'),**{'EXTRA.TXT':b'new official member'}))
    def test_yamaha_manifest_claim_cannot_change(self):
        files=yamaha(b'old Yamaha');record=json.loads(files['MANIFEST.JSN'])
        record['native_test']='a different claim'
        files['MANIFEST.JSN']=M.P.text(json.dumps(record))
        files['SHA256.SUM']=M.P.text(''.join(M.P.identity(b)['sha256']+'  '+n+'\n' for n,b in sorted(files.items()) if n!='SHA256.SUM'))
        with self.assertRaisesRegex(ValueError,'panning/installer/support'):self.check(previous_yamaha=files)
    def test_yamaha_manifest_must_describe_payload(self):
        files=yamaha(b'old Yamaha');files['YAM160.DRV']=b'unrecorded driver'
        with self.assertRaisesRegex(ValueError,'panning/installer/support'):self.check(previous_yamaha=files)
    def test_yamaha_checksum_must_be_exact(self):
        files=yamaha(b'old Yamaha');files['SHA256.SUM']+=b'unexpected\r\n'
        with self.assertRaisesRegex(ValueError,'panning/installer/support'):self.check(previous_yamaha=files)
    def test_yamaha_native_gate_cannot_be_skipped(self):
        with self.assertRaisesRegex(ValueError,'native evidence'):self.check(yamaha_error=ValueError('native evidence failed'))
    def test_colorplus_native_driver_binding(self):
        with self.assertRaisesRegex(ValueError,'native qualification'):
            self.check(qualification={'driver':M.P.identity(b'wrong driver')})
    def test_yamaha_source_packet_binding(self):
        (self.root/'yamaha').write_bytes(b'unqualified')
        with self.assertRaisesRegex(ValueError,'qualified source packet'):self.check()
    def test_pc1_cannot_change(self):
        with self.assertRaisesRegex(ValueError,'unaffected release asset'):self.check(live_overrides={'PC1.ZIP':b'different PC1'})
    def test_pc1_must_retain_source_pin(self):
        self.spec['local']['PC1.ZIP']['identity']=M.P.identity(b'other PC1')
        with self.assertRaisesRegex(ValueError,'Qualified PC1'):self.check()
    def test_unrelated_asset_cannot_change(self):
        with self.assertRaisesRegex(ValueError,'unaffected release asset'):self.check(live_overrides={'KEEP.ZIP':b'newer accepted bytes'})
    def test_unrelated_asset_cannot_be_missing(self):
        with self.assertRaisesRegex(ValueError,'asset closure'):self.check(missing=('KEEP.ZIP',))
    def test_duplicate_release_asset_rejected(self):
        with self.assertRaisesRegex(ValueError,'asset closure'):
            self.check(extra_rows=[{'name':'CPPAN.ZIP','size':1,'digest':'sha256:'+'0'*64}])
    def test_anonymous_download_must_match_metadata(self):
        with self.assertRaisesRegex(ValueError,'release metadata'):self.check(damage_metadata=True)
    def test_already_uploaded_packets_can_finish_catalog(self):
        self.check(dict(self.files),dict(self.yamaha))
    def test_interrupted_missing_allowlisted_packets_can_be_repaired(self):
        for name in M.PACKETS:
            with self.subTest(name=name):self.check(missing=(name,))
    def test_local_preparation_preserves_exact_unrelated_asset(self):
        pin=M.P.identity(b'unrelated');(self.out/'KEEP.ZIP').write_bytes(b'new broad-build collection')
        release={'assets':[{'name':'KEEP.ZIP','size':pin['bytes'],'digest':'sha256:'+pin['sha256'],'browser_download_url':'https://example.invalid/KEEP.ZIP'}]}
        with mock.patch.object(M,'PRESERVE_CURRENT',{'KEEP.ZIP':pin}),mock.patch.object(M,'download',return_value=b'unrelated'):
            M.prepare(self.out,release)
        self.assertEqual((self.out/'KEEP.ZIP').read_bytes(),b'unrelated')
        self.assertEqual(json.loads((self.out/'CURRENT.JSN').read_bytes())['preserved_current_assets'],{'KEEP.ZIP':pin})
        self.check()
    def test_unrecognized_unrelated_asset_is_not_adopted(self):
        pin=M.P.identity(b'unrelated');before=(self.out/'CURRENT.JSN').read_bytes()
        release={'assets':[{'name':'KEEP.ZIP','size':1,'digest':'sha256:'+'0'*64}]}
        with mock.patch.object(M,'PRESERVE_CURRENT',{'KEEP.ZIP':pin}),mock.patch.object(M,'download') as download:
            with self.assertRaisesRegex(ValueError,'unaffected current asset changed'):M.prepare(self.out,release)
            download.assert_not_called()
        self.assertEqual((self.out/'CURRENT.JSN').read_bytes(),before)

class Publication(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.folder=Path(self.temp.name)
        (self.folder/'CURRENT.JSN').write_text(json.dumps({'source_commit':'reviewed-head'}))
        self.expected={name:M.P.identity(name.encode()) for name in M.ORDER}
        self.events=[]
    def main(self,publish=True,env=None,head='reviewed-head',commit='reviewed-head',live_main=True):
        args=['CPPUB.PY','--folder',str(self.folder),'--commit',commit]+(['--publish'] if publish else [])
        environ={'GITHUB_REPOSITORY':M.REPOSITORY,'GITHUB_REF':'refs/heads/main','GITHUB_EVENT_NAME':'push','GITHUB_SHA':head}
        environ.update(env or {})
        def main_check(value):
            self.events.append(('main',value))
            if not live_main:raise ValueError('Main advanced')
        def upload(args,**kwargs):self.events.append(('upload',Path(args[4]).name))
        with mock.patch.object(sys,'argv',args),mock.patch.dict(os.environ,environ),mock.patch.object(M.subprocess,'check_output',return_value=head),mock.patch.object(M,'download',return_value=b'{}'),mock.patch.object(M,'check',return_value=(self.expected,{})),mock.patch.object(M,'require_live_main',side_effect=main_check),mock.patch.object(M.subprocess,'run',side_effect=upload),mock.patch.object(M,'readback',side_effect=lambda expected:self.events.append(('readback',expected))):
            M.main()
    def test_read_only_default_never_uploads(self):
        self.main(publish=False);self.assertEqual(self.events,[])
    def test_each_allowlisted_write_rechecks_main_then_readback(self):
        self.main()
        self.assertEqual(self.events,[(kind,value) for name in M.ORDER for kind,value in [('main','reviewed-head'),('upload',name)]]+[('readback',self.expected)])
    def test_stale_main_stops_before_any_write(self):
        with self.assertRaisesRegex(ValueError,'Main advanced'):self.main(live_main=False)
        self.assertEqual(self.events,[('main','reviewed-head')])
    def test_wrong_workflow_context_never_writes(self):
        for key,value in [('GITHUB_REPOSITORY','other/repo'),('GITHUB_REF','refs/heads/topic'),('GITHUB_EVENT_NAME','pull_request'),('GITHUB_SHA','other-head')]:
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'exact main push'):self.main(env={key:value})
        self.assertEqual(self.events,[])
    def test_catalog_and_cli_must_match_checkout(self):
        for options in ({'head':'other-head'},{'commit':'other-head'}):
            with self.subTest(options=options),self.assertRaisesRegex(ValueError,'exact catalog/source commit'):self.main(**options)
        self.assertEqual(self.events,[])
    def test_live_ref_is_exact(self):
        with mock.patch.object(M,'download',return_value=json.dumps({'object':{'sha':'new-head'}}).encode()):
            with self.assertRaisesRegex(ValueError,'Main advanced'):M.require_live_main('old-head')
            M.require_live_main('new-head')
    def test_duplicate_final_assets_fail_readback(self):
        bodies={name:name.encode() for name in M.ORDER}
        rows=[{'name':name,'size':pin['bytes'],'digest':'sha256:'+pin['sha256']} for name,pin in self.expected.items()]
        rows.append(dict(rows[0]))
        def download(url):
            return json.dumps({'assets':rows}).encode() if '/releases/tags/' in url else bodies[url.rsplit('/',1)[1]]
        with mock.patch.object(M,'download',side_effect=download),self.assertRaisesRegex(ValueError,'asset identities'):M.readback(self.expected)

if __name__=='__main__':unittest.main()
