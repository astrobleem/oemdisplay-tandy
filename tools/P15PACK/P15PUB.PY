"""Publish only a qualified PC1512 catalog update; preserve every other asset.

Default mode is read-only. Writes require --publish from the main-branch workflow
at its exact checked commit. Uses existing BUNDLE/CHECK and gh authentication.
"""
from pathlib import Path
import argparse,hashlib,importlib.machinery,json,os,subprocess,urllib.request
ROOT=Path(__file__).resolve().parents[2]
P=importlib.machinery.SourceFileLoader('p15_catalog',str(ROOT/'tools/CURRENT/BUNDLE.PY')).load_module()
V=importlib.machinery.SourceFileLoader('p15_release_proof',str(ROOT/'src/pc1512/P15VERIFY.PY')).load_module()
ORDER=('PC1512.ZIP','CURRENT.SHA','CURRENT.JSN')
CHANGED=set(ORDER)
REPOSITORY='astrobleem/oemdisplay-tandy'
URL='https://github.com/'+REPOSITORY+'/releases/download/windows-xt/'

def download(url):
    request=urllib.request.Request(url,headers={'User-Agent':'qualified-pc1512-publisher','Cache-Control':'no-cache'})
    return urllib.request.urlopen(request,timeout=60).read()

def check(folder,release):
    spec=P.spec(); expected={x.name:P.identity(x.read_bytes()) for x in folder.iterdir() if x.is_file()}
    record=json.loads((folder/'CURRENT.JSN').read_bytes())
    payload={n:pin for n,pin in expected.items() if n not in {'CURRENT.JSN','CURRENT.SHA'}}
    sums=P.text(''.join(pin['sha256']+'  '+n+'\n' for n,pin in sorted(expected.items()) if n!='CURRENT.SHA'))
    if record['assets']!=payload or (folder/'CURRENT.SHA').read_bytes()!=sums:
        raise ValueError('Catalog record/checksum closure differs')
    assets=release['assets']; actual={r['name']:{'bytes':r['size'],'sha256':r['digest'].removeprefix('sha256:')} for r in assets}
    if (release['tag_name']!='windows-xt' or release['draft'] or release['immutable'] or
        len(actual)!=len(assets) or set(actual)-set(expected) or (set(expected)-set(actual))-CHANGED):
        raise ValueError('Current release identity/asset closure differs')
    if any(actual.get(n)!=expected[n] for n in expected if n not in CHANGED):
        raise ValueError('An unaffected release asset differs; refusing all writes')
    if any(expected[n]!=pin for n,pin in spec['core_identities'].items()):
        raise ValueError('Qualified core assets differ')
    source=P.zip_files((ROOT/spec['local']['PC1512.ZIP']['source']).read_bytes())
    current=P.zip_files((folder/'PC1512.ZIP').read_bytes())
    overlay=spec['documentation_overlays']['PC1512.ZIP']
    if (set(current)!=set(source) or overlay['member']!='INSTALL.TXT' or
        current['INSTALL.TXT']!=(ROOT/overlay['source']).read_bytes() or
        any(current[n]!=source[n] for n in current if n!='INSTALL.TXT')):
        raise ValueError('Current PC1512 ZIP changed qualified runtime')
    qualification,_=V.verify()
    if P.identity(current['PC1512.DRV'])!=qualification['driver']:
        raise ValueError('Public PC1512 driver differs from native qualification')
    return expected,actual

def require_live_main(head):
    ref=json.loads(download('https://api.github.com/repos/'+REPOSITORY+'/git/ref/heads/main'))
    if ref['object']['sha']!=head:raise ValueError('Main advanced; refusing stale publication')

def readback(expected):
    for name in ORDER:
        if P.identity(download(URL+name))!=expected[name]:
            raise ValueError('Anonymous publication readback differs: '+name)
    after=json.loads(download('https://api.github.com/repos/'+REPOSITORY+'/releases/tags/windows-xt'))
    final={r['name']:{'bytes':r['size'],'sha256':r['digest'].removeprefix('sha256:')} for r in after['assets']}
    if final!=expected:raise ValueError('Published catalog asset identities differ')

def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument('--folder',type=Path,required=True)
    a.add_argument('--commit',required=True)
    a.add_argument('--publish',action='store_true')
    args=a.parse_args();folder=args.folder.resolve()
    record=json.loads((folder/'CURRENT.JSN').read_bytes())
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    if args.commit!=head or record['source_commit']!=head:
        raise ValueError('Publisher requires its exact catalog/source commit')
    release=json.loads(download('https://api.github.com/repos/'+REPOSITORY+'/releases/tags/windows-xt'))
    expected,actual=check(folder,release)
    print(json.dumps({'commit':head,'replacement_assets':sorted(CHANGED),
                      'unchanged_assets':len(expected)-len(CHANGED),'write_requested':args.publish},indent=2))
    if not args.publish:return
    if (os.environ.get('GITHUB_REPOSITORY')!=REPOSITORY or os.environ.get('GITHUB_REF')!='refs/heads/main' or
        os.environ.get('GITHUB_EVENT_NAME')!='push' or os.environ.get('GITHUB_SHA')!=head):
        raise ValueError('Publication is restricted to this exact main push')
    changed=[name for name in ORDER if actual.get(name)!=expected[name]]
    for name in changed:
        # Check immediately before each mutation; the final catalog record is
        # the commit marker. Missing allowlisted assets from a failed clobber
        # are repaired, while missing/unmatched unrelated assets are refused.
        require_live_main(head)
        subprocess.run(['gh','release','upload','windows-xt',str(folder/name),
                        '--clobber','--repo',REPOSITORY],check=True,cwd=ROOT)
    readback(expected)
    print('PASS: PC1512 ZIP and catalog read back; all other current assets preserved')

if __name__=='__main__':main()
