"""Build/publish only the eight graphics System-font OEM archives.

No native installer, checksums or inventory files are generated. Historical
full-install packets and all other release assets remain unchanged.
"""
from pathlib import Path
import argparse,importlib.machinery as M,io,json,os,subprocess,tempfile,time,urllib.request,zipfile
ROOT=Path(__file__).resolve().parents[2]
PREP=M.SourceFileLoader('system_oem',str(ROOT/'tools/FONTPACK/PREPARE.PY')).load_module()
PACKETS=(
 ('SFTANDY.ZIP','WINXT','tools/FONTPACK/BIN/WINXT.ZIP'),
 ('SFCGA.ZIP','CGA','downloads/FRESH/CGA.ZIP'),
 ('SFPCJR.ZIP','JRPAN','downloads/PAN/JRPAN.ZIP'),
 ('SFPCP.ZIP','CPPAN','downloads/PAN/CPPAN.ZIP'),
 ('SF1512.ZIP','PC1512','downloads/experimental/PC1512/PC1512.ZIP'),
 ('SFTGA2.ZIP','T2EXP','downloads/experimental/TGA2/TNDYV2.ZIP'),
 ('SFPC1.ZIP','PC1','downloads/experimental/yamaha/PC1.ZIP'),
 ('SFYAMA.ZIP','YAMAHA','downloads/experimental/yamaha/YAMAHA.ZIP'))
REPO='astrobleem/oemdisplay-tandy'
TAG='windows-xt'

def build(out):
 out.mkdir(parents=True,exist_ok=False)
 with tempfile.TemporaryDirectory() as tmp:
  for name,folder,source in PACKETS:
   tree=Path(tmp)/folder;PREP.drivers(tree,ROOT/source)
   with zipfile.ZipFile(out/name,'w',compression=zipfile.ZIP_STORED) as z:
    for p in sorted(tree.rglob('*')):
     if p.is_file():
      item=zipfile.ZipInfo(folder+'/'+p.relative_to(tree).as_posix(),(1980,1,1,0,0,0))
      item.create_system=0;item.external_attr=32;z.writestr(item,p.read_bytes())
   print('Built',name)

def verify(folder):
 with tempfile.TemporaryDirectory() as tmp:
  expected=Path(tmp)/'expected';build(expected)
  for name,root,source in PACKETS:
   data=(folder/name).read_bytes()
   if data!=(expected/name).read_bytes():raise ValueError('Archive differs: '+name)
   with zipfile.ZipFile(io.BytesIO(data)) as z:
    for member in z.namelist():
     if member.upper().endswith(('.JSN','.JSON','.SHA','.SUM')):raise ValueError('Unexpected record: '+member)
    for font in ('CG1SYS.FON','CG2SYS.FON','XTCSYS.FON','XTESYS.FON'):
     if root+'/'+font in z.namelist():
      if z.read(root+'/'+font)!=(ROOT/'tools/SYSFONT/BIN'/font).read_bytes():raise ValueError('System resource differs')
   print('PASS exact consumer archive',name)

def gh(*args):return subprocess.check_output(['gh',*args],text=True)
def download(url):
 req=urllib.request.Request(url,headers={'User-Agent':'Windows-XT-System-fonts','Cache-Control':'no-cache'})
 return urllib.request.urlopen(req,timeout=60).read()
def main_head():return json.loads(gh('api','repos/'+REPO+'/git/ref/heads/main'))['object']['sha']
def ready(folder):
 # Host-only release gate: the unchanged universal launcher rejects newly
 # resource-derived JR/ColorPlus drivers. Do not publish eight assets merely
 # because archive/font metadata passes; retain the guest binding unchanged.
 for name,root,source in PACKETS:
  if name not in ('SFPCJR.ZIP','SFPCP.ZIP'):continue
  with zipfile.ZipFile(folder/name) as z:now={Path(n).name:z.read(n) for n in z.namelist()}
  with zipfile.ZipFile(ROOT/source) as z:old={Path(n).name:z.read(n) for n in z.namelist()}
  driver='JRPAN.DRV' if name=='SFPCJR.ZIP' else 'CPPAN.DRV'
  if now.get('PANINST.EXE')==old.get('PANINST.EXE') and now[driver]!=old[driver]:
   raise ValueError('Publication held: unchanged PANINST rejects revised '+driver+'; qualify its existing binding before replacing '+name)

def publish(folder,commit):
 head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
 if not (commit==head==os.environ.get('GITHUB_SHA') and os.environ.get('GITHUB_REPOSITORY')==REPO and os.environ.get('GITHUB_EVENT_NAME')=='push' and os.environ.get('GITHUB_REF')=='refs/heads/main'):
  raise ValueError('Publication requires exact authorized main-push workflow')
 verify(folder)
 ready(folder)
 before=json.loads(gh('api','repos/'+REPO+'/releases/tags/'+TAG))
 allowed={n for n,_,_ in PACKETS}
 preserved={x['name']:(x['id'],x['size'],x['updated_at']) for x in before['assets'] if x['name'] not in allowed}
 for name,_,_ in PACKETS:
  if main_head()!=commit:raise ValueError('Main advanced; publication stopped')
  gh('release','upload',TAG,str(folder/name),'--clobber','--repo',REPO)
 for name,_,_ in PACKETS:
  url='https://github.com/'+REPO+'/releases/download/'+TAG+'/'+name
  for attempt in range(6):
   try:
    if download(url)!=(folder/name).read_bytes():raise ValueError('Anonymous content differs: '+name)
    break
   except Exception:
    if attempt==5:raise
    time.sleep(5)
  print('PASS anonymous public download',name)
 after=json.loads(gh('api','repos/'+REPO+'/releases/tags/'+TAG))
 actual={x['name']:(x['id'],x['size'],x['updated_at']) for x in after['assets'] if x['name'] not in allowed}
 if any(actual.get(name)!=row for name,row in preserved.items()):raise ValueError('Unrelated release assets changed')
 print('PASS preserved all unrelated release assets; exact publication commit',commit)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path);p.add_argument('--verify',type=Path);p.add_argument('--publish',type=Path);p.add_argument('--commit');a=p.parse_args()
 if sum(x is not None for x in (a.out,a.verify,a.publish))!=1:p.error('Choose one operation')
 if a.out:build(a.out)
 elif a.verify:verify(a.verify)
 else:publish(a.publish,a.commit)
