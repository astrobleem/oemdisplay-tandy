"""Publish qualified ColorPlus/Yamaha driver updates; preserve every other asset.

Default mode is read-only. Writes require --publish from the main-branch workflow
at its exact checked commit. Uses existing BUNDLE/CHECK and gh authentication.
"""
from pathlib import Path
import argparse,hashlib,importlib.machinery,json,os,subprocess,urllib.request
ROOT=Path(__file__).resolve().parents[2]
P=importlib.machinery.SourceFileLoader('p15_catalog',str(ROOT/'tools/CURRENT/BUNDLE.PY')).load_module()
V=importlib.machinery.SourceFileLoader('p15_release_proof',str(ROOT/'src/pcp/CPVERIFY.PY')).load_module()
PACKETS=('CPPAN.ZIP','YAMAHA.ZIP')
ORDER=PACKETS+('CURRENT.SHA','CURRENT.JSN')
CHANGED=set(ORDER)
# This driver-only publisher preserves the current accepted collection.
# Shared helper/core updates are outside this publisher's scope.
PRESERVE_CURRENT={'TANDYLAB.ZIP':{'bytes':1098337,'sha256':'d50f4563d42b4219af093a0bb260fcf4d1cdbb495a69cf3cfa6ad0b31c67654e'}}
REPOSITORY='astrobleem/oemdisplay-tandy'
URL='https://github.com/'+REPOSITORY+'/releases/download/windows-xt/'

def download(url):
    request=urllib.request.Request(url,headers={'User-Agent':'qualified-colorplus-publisher','Cache-Control':'no-cache'})
    return urllib.request.urlopen(request,timeout=60).read()

def packet_files(data):
    files=P.zip_files(data)
    if P.archive(files)!=data:raise ValueError('Noncanonical current driver packet')
    return files

def driver_only(previous,current):
    # This is only a scope filter. check() binds INSTALL.TXT to its exact
    # qualified derivation before any publication can proceed.
    allowed={'PCP3216.DRV','INSTALL.TXT'}
    return (allowed<=set(current) and set(previous)==set(current) and
            all(previous[n]==current[n] for n in current if n not in allowed))

def yamaha_driver_only(previous,current):
    """Allow the B800 driver and its derived file records, never support edits."""
    allowed={'YAM160.DRV','MANIFEST.JSN','SHA256.SUM'}
    if (not allowed<=set(current) or set(previous)!=set(current) or
        any(previous[n]!=current[n] for n in current if n not in allowed)):
        return False
    records=[]
    for files in (previous,current):
        record=json.loads(files['MANIFEST.JSN'])
        pins={n:P.identity(b) for n,b in sorted(files.items()) if n not in {'MANIFEST.JSN','SHA256.SUM'}}
        sums=P.text(''.join(P.identity(b)['sha256']+'  '+n+'\n' for n,b in sorted(files.items()) if n!='SHA256.SUM'))
        if (not isinstance(record,dict) or record.get('profile')!='b800' or record.get('driver')!='YAM160.DRV' or
            record.get('files')!=pins or files['SHA256.SUM']!=sums):
            return False
        records.append({n:v for n,v in record.items() if n!='files'})
    return records[0]==records[1]

def yamaha_verify(data):
    gate=importlib.machinery.SourceFileLoader('fixed_yamaha_proof',str(ROOT/'tools/YAMPACK/PACK.PY')).load_module()
    return gate.verify('b800',data)

def optimized_guide(original):
    gate=importlib.machinery.SourceFileLoader('fixed_colorplus_guide',str(ROOT/'tools/CPPACK/CURRENT.PY')).load_module()
    return gate.install_guide(original)

def preserves_packet(name,previous,current):
    if name=='CPPAN.ZIP':return driver_only(previous,current)
    if name=='YAMAHA.ZIP':return yamaha_driver_only(previous,current)
    raise ValueError('Packet is outside fixed-driver scope: '+name)

def scope(folder,release):
    """Read-only workflow filter. Full qualification remains mandatory in check."""
    rows={name:[row for row in release['assets'] if row['name']==name] for name in ORDER}
    if any(len(r)>1 for r in rows.values()):raise ValueError('Duplicate current driver/catalog assets')
    data={name:(folder/name).read_bytes() for name in PACKETS}
    wanted={name:P.identity(body) for name,body in data.items()}
    actual={name:({'bytes':r[0]['size'],'sha256':r[0]['digest'].removeprefix('sha256:')} if r else None) for name,r in rows.items()}
    changed=any(actual[name]!=wanted[name] for name in PACKETS)
    if not changed:
        changed=any(not rows[name] for name in ('CURRENT.JSN','CURRENT.SHA'))
        if not changed:
            bodies={name:download(rows[name][0]['browser_download_url']) for name in ('CURRENT.JSN','CURRENT.SHA')}
            if any(P.identity(body)!=actual[name] for name,body in bodies.items()):
                raise ValueError('Current catalog download differs')
            record=json.loads(bodies['CURRENT.JSN'])
            sums={name:digest for digest,name in (line.split('  ',1) for line in bodies['CURRENT.SHA'].decode('ascii').splitlines())}
            changed=(any(record['assets'].get(name)!=wanted[name] or sums.get(name)!=wanted[name]['sha256'] for name in PACKETS) or
                     sums.get('CURRENT.JSN')!=P.identity(bodies['CURRENT.JSN'])['sha256'])
    within=True
    if changed:
        for name in PACKETS:
            if not rows[name]:continue
            previous=download(rows[name][0]['browser_download_url'])
            if P.identity(previous)!=actual[name]:raise ValueError('Current driver download differs: '+name)
            within=preserves_packet(name,packet_files(previous),packet_files(data[name])) and within
    return changed,within


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
    if expected.get('PC1.ZIP')!=spec['local']['PC1.ZIP']['identity']:
        raise ValueError('Qualified PC1 packet differs')
    source=packet_files((ROOT/spec['local']['CPPAN.ZIP']['source']).read_bytes())
    current=packet_files((folder/'CPPAN.ZIP').read_bytes())
    overlay=spec['documentation_overlays']['CPPAN.ZIP']
    qualification,_=V.verify()
    transform=overlay.get('transform')
    if transform!=('optimized-colorplus' if qualification.get('optimized') else None):
        raise ValueError('Unrecognized or unqualified ColorPlus guide transform')
    guide=(ROOT/overlay['source']).read_bytes()
    if qualification.get('optimized'):guide=optimized_guide(guide)
    if (set(current)!=set(source) or overlay['member']!='INSTALL.TXT' or
        any(current[n]!=source[n] for n in current if n!='INSTALL.TXT')):
        raise ValueError('Current ColorPlus ZIP changed qualified runtime')
    if current['INSTALL.TXT']!=guide:
        raise ValueError('Current ColorPlus installation guide differs from qualified derivation')
    if P.identity(current['PCP3216.DRV'])!=qualification['driver']:
        raise ValueError('Public ColorPlus driver differs from native qualification')
    yamaha=(folder/'YAMAHA.ZIP').read_bytes()
    yamaha_source=spec['local']['YAMAHA.ZIP']
    if (P.identity(yamaha)!=yamaha_source['identity'] or
        yamaha!=(ROOT/yamaha_source['source']).read_bytes()):
        raise ValueError('Current Yamaha ZIP differs from qualified source packet')
    yamaha_verify(yamaha)
    # A concurrent panning/settings release shares this ZIP. Even though the
    # archive itself is allowlisted for replacement, preserve support/runtime
    # members besides the fixed driver and verified derived installation guide.
    # A missing archive can be repaired from the exact native
    # qualified packet after an interrupted allowlisted upload.
    for name in PACKETS:
        live=[r for r in assets if r['name']==name]
        if live:
            data=download(live[0]['browser_download_url'])
            if P.identity(data)!=actual[name]:
                raise ValueError('Anonymous current driver ZIP differs from release metadata: '+name)
            if not preserves_packet(name,packet_files(data),packet_files((folder/name).read_bytes())):
                raise ValueError('Fixed-driver update would replace panning/installer/support members: '+name)
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
    if len(final)!=len(after['assets']) or final!=expected:raise ValueError('Published catalog asset identities differ')

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
    print('PASS: ColorPlus/Yamaha ZIPs and catalog read back; all other current assets preserved')

if __name__=='__main__':main()
