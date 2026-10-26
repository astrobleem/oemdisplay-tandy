"""Publish only a qualified ColorPlus catalog update; preserve every other asset.

Default mode is read-only. Writes require --publish from the main-branch workflow
at its exact checked commit. Uses existing BUNDLE/CHECK and gh authentication.
"""
from pathlib import Path
import argparse,hashlib,importlib.machinery,json,os,subprocess,urllib.request
ROOT=Path(__file__).resolve().parents[2]
P=importlib.machinery.SourceFileLoader('p15_catalog',str(ROOT/'tools/CURRENT/BUNDLE.PY')).load_module()
V=importlib.machinery.SourceFileLoader('p15_release_proof',str(ROOT/'src/pcp/CPVERIFY.PY')).load_module()
ORDER=('CPPAN.ZIP','CURRENT.SHA','CURRENT.JSN')
CHANGED=set(ORDER)
# This driver-only publisher preserves the current accepted collection.
# Shared helper/core updates use aggregate current-release publication.
PRESERVE_CURRENT={'TANDYLAB.ZIP':{'bytes':959948,'sha256':'8c6a7d016293658a84ba71c2ec633b8845bd4e81d09dadcad95436e76b5694cd'}}
REPOSITORY='astrobleem/oemdisplay-tandy'
URL='https://github.com/'+REPOSITORY+'/releases/download/windows-xt/'

def download(url):
    request=urllib.request.Request(url,headers={'User-Agent':'qualified-colorplus-publisher','Cache-Control':'no-cache'})
    return urllib.request.urlopen(request,timeout=60).read()

def driver_only(previous,current):
    return (set(previous)==set(current) and
            all(previous[n]==current[n] for n in current if n!='PCP3216.DRV'))


def prepare(folder,release):
    """Prepare local catalog artifacts, never mutate the release."""
    record=json.loads((folder/'CURRENT.JSN').read_bytes())
    for name,pin in PRESERVE_CURRENT.items():
        rows=[r for r in release['assets'] if r['name']==name]
        if len(rows)!=1 or {'bytes':rows[0]['size'],'sha256':rows[0]['digest'].removeprefix('sha256:')}!=pin:
            raise ValueError('Pinned unaffected current asset changed: '+name)
        path=folder/name
        if P.identity(path.read_bytes())!=pin:
            data=download(rows[0]['browser_download_url'])
            if P.identity(data)!=pin:raise ValueError('Unaffected current asset download differs: '+name)
            path.write_bytes(data)
        record['assets'][name]=pin
    record['preserved_current_assets']=PRESERVE_CURRENT
    (folder/'CURRENT.JSN').write_bytes(P.text(json.dumps(record,indent=2)+'\n'))
    (folder/'CURRENT.SHA').write_bytes(P.text(''.join(P.identity(p.read_bytes())['sha256']+'  '+p.name+'\n' for p in sorted(folder.iterdir()) if p.is_file() and p.name!='CURRENT.SHA')))

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
    source=P.zip_files((ROOT/spec['local']['CPPAN.ZIP']['source']).read_bytes())
    current=P.zip_files((folder/'CPPAN.ZIP').read_bytes())
    overlay=spec['documentation_overlays']['CPPAN.ZIP']
    if (set(current)!=set(source) or overlay['member']!='INSTALL.TXT' or
        current['INSTALL.TXT']!=(ROOT/overlay['source']).read_bytes() or
        any(current[n]!=source[n] for n in current if n!='INSTALL.TXT')):
        raise ValueError('Current ColorPlus ZIP changed qualified runtime')
    qualification,_=V.verify()
    if P.identity(current['PCP3216.DRV'])!=qualification['driver']:
        raise ValueError('Public ColorPlus driver differs from native qualification')
    # A concurrent panning/settings release shares this ZIP. Even though the
    # archive itself is allowlisted for replacement, preserve every other
    # live member. A missing archive can be repaired from the exact native
    # qualified packet after an interrupted allowlisted upload.
    live=[r for r in assets if r['name']=='CPPAN.ZIP']
    if live:
        data=download(live[0]['browser_download_url'])
        if P.identity(data)!=actual['CPPAN.ZIP']:
            raise ValueError('Anonymous current ColorPlus ZIP differs from release metadata')
        previous=P.zip_files(data)
        if not driver_only(previous,current):
            raise ValueError('Fixed ColorPlus update would replace panning/installer/support members')
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
    a.add_argument('--prepare',action='store_true',help='Preserve pinned unaffected bytes in local catalog artifacts; no release writes')
    args=a.parse_args();folder=args.folder.resolve()
    if args.prepare and args.publish:a.error('Prepare and publication are separate operations')
    record=json.loads((folder/'CURRENT.JSN').read_bytes())
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    if args.commit!=head or record['source_commit']!=head:
        raise ValueError('Publisher requires its exact catalog/source commit')
    release=json.loads(download('https://api.github.com/repos/'+REPOSITORY+'/releases/tags/windows-xt'))
    if args.prepare:prepare(folder,release)
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
    print('PASS: ColorPlus ZIP and catalog read back; all other current assets preserved')

if __name__=='__main__':main()
