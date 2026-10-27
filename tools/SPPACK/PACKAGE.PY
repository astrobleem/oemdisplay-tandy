"""Build the two qualified software-panning downloads with supplied support."""
from pathlib import Path
import argparse,hashlib,io,json,zipfile,importlib.machinery
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
L=importlib.machinery.SourceFileLoader('sp_historical_sources',str(ROOT/'tools/LEGACY/SOURCE.PY')).load_module()
STAMP=(2026,10,24,0,0,0)
ASSETS={'JRPAN.ZIP','CPPAN.ZIP','README.TXT','RELEASE.JSON','SHA256SUMS'}
def identity(b):return {'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def dos(s):return s.replace('\r\n','\n').replace('\n','\r\n').encode('ascii')
def js(v):return dos(json.dumps(v,indent=2,sort_keys=True)+'\n')

def supplied_grabber():
    decoder=importlib.machinery.SourceFileLoader('sp_expand',str(ROOT/'tools/XR1PACK/PREPARE.PY')).load_module()
    return decoder.expanded_file((ROOT/'distributions/WINXT/CGA.GR2').read_bytes(),'CGA.GR2')
def payload(kind,spec):
    ui=importlib.machinery.SourceFileLoader('sp_qualified_settings',str(ROOT/'src/panui/VERIFY.PY')).load_module()
    qualification,binaries=ui.verify()
    native_path='docs/QUAL/WDESK/NATIVE.JSN'
    if spec['qualification']['ui_update']!={'path':native_path,'manifest':identity((ROOT/native_path).read_bytes())}:
        raise ValueError('Changed native settings qualification manifest')
    base=HERE/'PAYLOAD'/kind
    expected=spec['profiles'][kind]['files']
    actual={p.name:p.read_bytes() for p in base.iterdir() if p.is_file()}
    if set(actual)!=set(expected):raise ValueError('Unexpected payload files '+kind)
    for n,b in actual.items():
        if identity(b)!=expected[n]:raise ValueError('Changed qualified payload '+kind+'/'+n)
    for n in ('XTPAN.EXE','PANCFG.EXE'):
        if actual[n]!=binaries[n]:raise ValueError('Different native-qualified settings helper '+kind+'/'+n)
    if kind=='CPPAN' and actual['CGA.GR2']!=supplied_grabber():raise ValueError('Changed supplied CGA grabber')
    return actual
def archive(kind,files):
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
        for n,b in sorted(files.items()):
            info=zipfile.ZipInfo(kind+'/'+n,STAMP);info.create_system=0;info.external_attr=0x20
            info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,b)
    return out.getvalue()
def outputs():
    spec=json.loads((HERE/'PUBLIC.JSN').read_bytes())
    if not spec['publication_allowed'] or spec['hardware_panning']:raise ValueError('Wrong publication state')
    for n,pin in spec['source'].items():
        if identity(L.source(n,(ROOT/n).read_bytes(),pin))!=pin:raise ValueError('Changed qualified source '+n)
    files={kind+'.ZIP':archive(kind,payload(kind,spec)) for kind in ('JRPAN','CPPAN')}
    files['README.TXT']=(HERE/'README.TXT').read_bytes()
    release={'schema':2,'tag':spec['tag'],'publication_allowed':True,'hardware_panning':False,
             'bundled_windows_support_files':spec['bundled_windows_support_files'],'logical':[320,400],'viewport':[320,200],
             'shadow_bytes':64000,'additional_shadow_bytes':32000,'profiles':spec['profiles'],
             'source':spec.get('published_source',spec['source']),'qualification':spec['qualification'],
             'assets':{n:identity(b) for n,b in sorted(files.items())}}
    files['RELEASE.JSON']=js(release)
    files['SHA256SUMS']=dos(''.join(identity(b)['sha256']+'  '+n+'\n' for n,b in sorted(files.items())))
    return files
def verify(out):
    files=outputs()
    if {p.name for p in out.iterdir()}!=ASSETS:raise ValueError('Wrong public asset set')
    for n,b in files.items():
        if (out/n).read_bytes()!=b:raise ValueError('Nonreproducible public asset '+n)
    return {n:identity(b) for n,b in files.items()}
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path);p.add_argument('--verify',type=Path);a=p.parse_args()
    if bool(a.out)==bool(a.verify):p.error('Choose --out or --verify')
    if a.out:
        a.out.mkdir(parents=True,exist_ok=False)
        for n,b in outputs().items():(a.out/n).write_bytes(b)
        result=verify(a.out)
    else:result=verify(a.verify)
    print(json.dumps({'pass':True,'assets':result},indent=2))
if __name__=='__main__':main()
