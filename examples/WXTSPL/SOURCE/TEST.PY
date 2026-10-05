from pathlib import Path
import tempfile,itertools,subprocess,json,hashlib,shutil,argparse
P=Path(__file__).resolve().parent
parser=argparse.ArgumentParser(description="Non-mutating-input host safety suite; temporary copies only.")
parser.add_argument('--exe',type=Path,required=True,help='Compiled HOST_TEST executable')
parser.add_argument('--stock-win-com',type=Path,required=True,help='Your recognized 11118-byte stock WIN.COM')
parser.add_argument('--old-tandy-rle',type=Path,required=True,help='Existing first-party src/splash/assets/TNDYLOGO.RLE')
parser.add_argument('--report',type=Path,help='Optional JSON output; never overwrites an existing report')
args=parser.parse_args()
EXE=args.exe.resolve()
if args.report and args.report.exists():parser.error('Choose a new report filename')
old=args.stock_win_com.read_bytes()
assert len(old)==11118 and hashlib.sha256(old).hexdigest()=='5551ebcd3f32df26f759c5423f806733e006c3cae640a8336e5c618f8d899659', 'Unrecognized private stock WIN.COM'
rle=(P.parent/'WXTSPL01.RLE').read_bytes()
assert hashlib.sha256(rle).hexdigest()=='eec3a413bb776bea8eccb19a379428d15f06cbdc0ac41b0871345ff9c24caf1c'
old_rle=args.old_tandy_rle.read_bytes()
assert hashlib.sha256(old_rle).hexdigest()=='e7a9c043ce3b9f9c78f7ff38bc68d211a0da32462e036abb7135f0602194f083'
tandy=old[:4336]+old_rle
new=old[:4336]+rle
DATA={1:old,2:tandy,3:new,4:b'unknown'}
names=['WIN.COM','WIN.WXB','WIN.WXN']
def snap(p):
 return {str(f.relative_to(p)):('link',str(f.readlink())) if f.is_symlink() else ('dir',) if f.is_dir() else ('file',f.read_bytes()) for f in p.rglob('*')}
def make(p,k,n):
 if k==0:return
 if k in DATA:(p/n).write_bytes(DATA[k])
 if k==5:(p/n).mkdir()
 if k==6:(p/n).symlink_to(p/'sentinel')
def allowed(mode,l,b,n):
 if mode=='CHECK':return l in (1,2) and b==0 and n in(0,3) or l==3 and b in(0,1,2) and n==0 or l==0 and b in(1,2) and n in(0,3)
 if mode=='APPLY':return allowed('CHECK',l,b,n)
 return l in(1,2) and b==0 or l==0 and b in(1,2) or l==3 and b in(1,2) and n==0
count=0
with tempfile.TemporaryDirectory(prefix='wxt-test-') as td:
 root=Path(td)
 for mode in ['CHECK','APPLY','RESTORE']:
  for l,b,n in itertools.product(range(7),repeat=3):
   p=root/'case';p.mkdir();(p/'sentinel').write_bytes(b'unchanged');(p/'SYSTEM.INI').write_bytes(b'display.drv=TR43216.DRV\r\n');(p/'driver.drv').write_bytes(b'latest-driver');(p/'font.fon').write_bytes(b'latest-font')
   for k,name in zip((l,b,n),names):make(p,k,name)
   (root/'WXTSPL01.RLE').write_bytes(rle)
   before=snap(p);r=subprocess.run([str(EXE),mode,str(p)],cwd=root,capture_output=True)
   ok=allowed(mode,l,b,n)
   assert (r.returncode==0)==ok,(mode,l,b,n,r.stdout)
   after=snap(p)
   if not ok or mode=='CHECK':assert before==after,(mode,l,b,n,'mutation on refusal/read')
   assert all(after[x]==before[x] for x in ['sentinel','SYSTEM.INI','driver.drv','font.fon'])
   if ok and mode=='APPLY':
    assert (p/'WIN.COM').read_bytes()==new
    if l in(1,2):assert (p/'WIN.WXB').read_bytes()==DATA[l]
    if b in(1,2):assert (p/'WIN.WXB').read_bytes()==DATA[b]
   if ok and mode=='RESTORE':
    assert (p/'WIN.COM').read_bytes()==DATA[l if l in(1,2) else b]
   shutil.rmtree(p);count+=1
 # Bad artifact / missing artifact / exact supported variants.
 for art in [None,rle[:-1],rle+b'X',bytes([rle[0]^1])+rle[1:]]:
  p=root/'bad';p.mkdir();(p/'WIN.COM').write_bytes(old)
  a=root/'WXTSPL01.RLE'
  if a.exists():a.unlink()
  if art is not None:a.write_bytes(art)
  before=snap(p);r=subprocess.run([str(EXE),'APPLY',str(p)],cwd=root,capture_output=True);assert r.returncode!=0 and snap(p)==before;shutil.rmtree(p);count+=1
 # Apply twice, restore twice, apply again; backup never overwritten.
 for o in [old,tandy]:
  p=root/'repeat';p.mkdir();(p/'WIN.COM').write_bytes(o);(root/'WXTSPL01.RLE').write_bytes(rle)
  for cmd in ['CHECK','APPLY','APPLY','RESTORE','RESTORE','APPLY']:
   r=subprocess.run([str(EXE),cmd,str(p)],cwd=root,capture_output=True);assert r.returncode==0,r.stdout;count+=1
  assert (p/'WIN.WXB').read_bytes()==o;shutil.rmtree(p)
 # Corrupted original prefix/tail/trailing bytes must not mutate.
 for o in [bytes([old[0]^1])+old[1:],old[:-1]+b'X',old+b'X']:
  p=root/'corrupt';p.mkdir();(p/'WIN.COM').write_bytes(o);before=snap(p);r=subprocess.run([str(EXE),'APPLY',str(p)],cwd=root,capture_output=True);assert r.returncode and snap(p)==before;shutil.rmtree(p);count+=1
print('PASS',count,'state/mutation/repeat/corruption tests')
if args.report: args.report.write_text(json.dumps({'pass':True,'cases':count,'state_grid':'7^3 combinations * CHECK/APPLY/RESTORE','kinds':['absent','exact stock','exact old Tandy','exact new','unknown bytes','directory','symlink'],'all_unrelated_sentinels_unchanged':True,'unknown_states_read_only':True},indent=2)+'\n')
