"""Exercise draft lookup, exact-source guards and published download checks."""
from pathlib import Path
import copy,hashlib,importlib.machinery,tempfile,unittest,urllib.parse
M=importlib.machinery.SourceFileLoader('sp_release',str(Path(__file__).with_name('RELEASE.PY'))).load_module()
SOURCE='a'*40;OLD='b'*40;REPO='owner/repo'

class Fake:
    def __init__(self,files,target=OLD,draft=True,present=(),tag=None):
        self.files=files;self.mutations=[];self.tag=tag;self.fail_listing=False
        self.release={'id':423143949,'tag_name':M.TAG,'target_commitish':target,'draft':draft,'assets':[self.asset(n) for n in present]}
    def asset(self,n):return {'name':n,'size':len(self.files[n]),'digest':'sha256:'+hashlib.sha256(self.files[n]).hexdigest(),'browser_download_url':'https://github.com/'+REPO+'/releases/download/'+M.TAG+'/'+n}
    def api(self,method,path,data=None,body=None):
        if method!='GET':self.mutations.append((method,path,data))
        if '/releases/tags/' in path:raise AssertionError('Drafts cannot be resolved by this endpoint')
        if method=='GET' and '/git/ref/tags/' in path:
            if self.tag is None:raise M.ApiError(404,'no tag')
            return {'object':{'type':'commit','sha':self.tag}}
        if method=='GET' and '/releases?' in path:
            if self.fail_listing:raise M.ApiError(403,'listing denied')
            return [copy.deepcopy(self.release)] if self.release else []
        if method=='POST' and path.endswith('/releases'):
            assert self.release is None;self.release={**data,'id':423143949,'assets':[]};return copy.deepcopy(self.release)
        if method=='POST' and '/assets?name=' in path:
            n=urllib.parse.parse_qs(urllib.parse.urlsplit(path).query)['name'][0];assert body==self.files[n]
            assert n not in {a['name'] for a in self.release['assets']};self.release['assets'].append(self.asset(n));return self.asset(n)
        if method=='POST' and path.endswith('/git/refs'):self.tag=data['sha'];return {'object':{'type':'commit','sha':self.tag}}
        if path.endswith('/releases/423143949'):
            if method=='PATCH':self.release.update(data)
            return copy.deepcopy(self.release)
        raise AssertionError((method,path))
    def download(self,url,limit):return self.files[url.rsplit('/',1)[1]][:limit]

class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)/'release-softpan';self.root.mkdir()
        self.files={n:('qualified '+n).encode() for n in M.NAMES}
        for n,b in self.files.items():(self.root/n).write_bytes(b)
        self.expected={n:hashlib.sha256(b).hexdigest() for n,b in self.files.items()}
    def tearDown(self):self.tmp.cleanup()
    def run_publish(self,f,download=None):return M.publish(REPO,SOURCE,self.root,self.expected,api=f.api,download=download or f.download)
    def test_observed_empty_untagged_draft_resumes_by_id(self):
        f=Fake(self.files);result=self.run_publish(f);self.assertTrue(result['pass']);self.assertEqual(f.tag,SOURCE)
        self.assertEqual(sum('/assets?name=' in p for _,p,_ in f.mutations),5)
        self.assertFalse(any(p.endswith('/releases') for _,p,_ in f.mutations));self.assertFalse(f.release['draft'])
        self.assertEqual((self.root.parent/'downloaded-softpan/JRPAN.ZIP').read_bytes(),self.files['JRPAN.ZIP'])
    def test_missing_release_uses_creation_id(self):
        f=Fake(self.files);f.release=None;self.assertTrue(self.run_publish(f)['pass'])
    def test_partial_correct_draft_uploads_only_missing(self):
        f=Fake(self.files,target=SOURCE,present=('JRPAN.ZIP','README.TXT'));self.run_publish(f)
        self.assertEqual(sum('/assets?name=' in p for _,p,_ in f.mutations),3)
    def test_other_tag_ref_is_preserved(self):
        f=Fake(self.files,tag=OLD)
        with self.assertRaises(AssertionError):self.run_publish(f)
        self.assertEqual(f.mutations,[])
    def test_nonempty_or_published_other_source_is_preserved(self):
        for draft,present in ((True,('README.TXT',)),(False,())):
            f=Fake(self.files,draft=draft,present=present)
            with self.assertRaises(AssertionError):self.run_publish(f)
            self.assertEqual(f.mutations,[])
    def test_existing_asset_digest_mismatch_is_preserved(self):
        f=Fake(self.files,target=SOURCE,present=('README.TXT',));f.release['assets'][0]['digest']='sha256:'+'0'*64
        with self.assertRaises(AssertionError):self.run_publish(f)
        self.assertEqual(f.mutations,[])
    def test_api_denial_does_not_create_another_draft(self):
        f=Fake(self.files);f.fail_listing=True
        with self.assertRaises(M.ApiError):self.run_publish(f)
        self.assertEqual(f.mutations,[])
    def test_published_correct_release_is_read_only(self):
        f=Fake(self.files,target=SOURCE,draft=False,present=M.NAMES,tag=SOURCE);self.run_publish(f);self.assertEqual(f.mutations,[])
    def test_bad_public_download_is_detected(self):
        f=Fake(self.files,target=SOURCE)
        with self.assertRaises(AssertionError):self.run_publish(f,lambda url,limit:b'wrong bytes')

if __name__=='__main__':unittest.main()
