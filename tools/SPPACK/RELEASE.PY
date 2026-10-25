"""Publish the verified panning assets, resuming drafts by release ID."""
from pathlib import Path
import hashlib,json,os,re,urllib.error,urllib.parse,urllib.request

NAMES={'JRPAN.ZIP','CPPAN.ZIP','README.TXT','RELEASE.JSON','SHA256SUMS'}
TAG='experimental-softpan-2026-10-24'

class ApiError(RuntimeError):
    def __init__(self,status,message):super().__init__(message);self.status=status

def github(method,path,data=None,body=None):
    url=path if path.startswith('https://uploads.github.com/') else 'https://api.github.com/'+path
    headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Accept':'application/vnd.github+json',
             'X-GitHub-Api-Version':'2022-11-28','User-Agent':'softpan-release'}
    if data is not None:body=json.dumps(data).encode();headers['Content-Type']='application/json'
    elif body is not None:headers['Content-Type']='application/octet-stream'
    try:
        with urllib.request.urlopen(urllib.request.Request(url,data=body,headers=headers,method=method),timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as e:raise ApiError(e.code,method+' '+path+' HTTP '+str(e.code)) from e

def public_download(url,limit):
    request=urllib.request.Request(url,headers={'User-Agent':'softpan-release'})
    with urllib.request.urlopen(request,timeout=30) as response:return response.read(limit)

def publish(repo,source,root,expected,api=github,download=public_download):
    assert re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',repo)
    assert re.fullmatch('[0-9a-f]{40}',source) and set(expected)==NAMES
    root=Path(root);files={n:(root/n).read_bytes() for n in NAMES}
    assert all(hashlib.sha256(b).hexdigest()==expected[n] for n,b in files.items())
    prefix='repos/'+repo;refpath=prefix+'/git/ref/tags/'+TAG
    def ref():
        try:return api('GET',refpath)
        except ApiError as e:
            if e.status==404:return None
            raise
    def exact_ref(value):
        assert value and value['object']['type']=='commit' and value['object']['sha']==source,'Existing tag belongs to another commit'
    tagref=ref()
    if tagref:exact_ref(tagref)
    matches=[]
    for page in range(1,11):
        releases=api('GET',prefix+'/releases?per_page=100&page='+str(page))
        matches.extend(x for x in releases if x['tag_name']==TAG)
        if len(releases)<100:break
    else:raise RuntimeError('Release listing bound reached')
    assert len(matches)<=1,'Duplicate release drafts; refusing ambiguous publication'
    if matches:release=matches[0]
    else:
        release=api('POST',prefix+'/releases',data={'tag_name':TAG,'target_commitish':source,
            'name':'PCjr and ColorPlus software panning','body':files['README.TXT'].decode(),
            'draft':True,'prerelease':True})
    rid=release['id'];path=prefix+'/releases/'+str(rid);release=api('GET',path)
    if release['target_commitish']!=source:
        assert release['draft'] and not release['assets'] and tagref is None,'Cannot retarget a nonempty, tagged or published release'
        api('PATCH',path,data={'target_commitish':source})
        release=api('GET',path)
    assert release['tag_name']==TAG and release['target_commitish']==source
    present=set()
    for asset in release['assets']:
        n=asset['name'];assert n in expected and n not in present,'Unexpected existing asset'
        assert asset.get('digest')=='sha256:'+expected[n],'Existing asset differs; refusing overwrite'
        assert asset['size']==len(files[n]);present.add(n)
    if not release['draft']:assert present==NAMES,'Published release is incomplete'
    for n in sorted(NAMES-present):
        api('POST','https://uploads.github.com/'+prefix+'/releases/'+str(rid)+'/assets?name='+urllib.parse.quote(n),body=files[n])
    release=api('GET',path)
    assert {a['name'] for a in release['assets']}==NAMES
    assert all(a.get('digest')=='sha256:'+expected[a['name']] and a['size']==len(files[a['name']]) for a in release['assets'])
    tagref=ref()
    if tagref is None:
        api('POST',prefix+'/git/refs',data={'ref':'refs/tags/'+TAG,'sha':source});tagref=ref()
    exact_ref(tagref)
    if release['draft']:api('PATCH',path,data={'draft':False,'prerelease':True})
    release=api('GET',path);assert not release['draft'] and release['target_commitish']==source
    downloaded=root.parent/'downloaded-softpan';downloaded.mkdir(exist_ok=False)
    for asset in release['assets']:
        n=asset['name'];url=asset['browser_download_url']
        assert url=='https://github.com/'+repo+'/releases/download/'+TAG+'/'+n
        b=download(url,len(files[n])+1)
        assert len(b)==len(files[n]) and hashlib.sha256(b).hexdigest()==expected[n],'Published download differs: '+n
        (downloaded/n).write_bytes(b)
    return {'release_id':rid,'tag':TAG,'source':source,'downloaded_sha256':expected,'pass':True}

if __name__=='__main__':
    print(json.dumps(publish(os.environ['GH_REPO'],os.environ['SOURCE_SHA'],Path('release-softpan'),
                             json.loads(Path('expected.json').read_text())),indent=2,sort_keys=True))
