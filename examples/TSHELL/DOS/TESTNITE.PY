#!/usr/bin/env python3
"""Run the exact renderer through BIOS/DOS stubs and recovery output guards."""
from pathlib import Path
import subprocess, tempfile, json, os, hashlib, re
P=Path(__file__).parent
src=(P/'SHELLSEL.C').read_text()
block=src.split('#ifndef HOST_TEST\nstatic unsigned char night_page;',1)[1].split('\n#endif\nstatic void restored_notice',1)[0]
block='static unsigned char night_page;'+block
stub=r'''
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
union REGS { struct { unsigned short ax,bx,cx,dx,si,di,cflag; } x;
 struct { unsigned char al,ah,bl,bh,cl,ch,dl,dh; } h; };
static unsigned char grid[25][80],attrs[25][80];
static unsigned mode,cols,page,flags,ioerr,row,col,video_calls,hidden;
static void intdos(union REGS *in,union REGS *out)
{ assert(in->x.ax==0x4400 && in->x.bx==1); out->x.cflag=ioerr;out->x.dx=flags; }
static void int86(unsigned n,union REGS *in,union REGS *out)
{ unsigned x,y; assert(n==0x10);++video_calls;
 switch(in->h.ah) {
 case 0x0f:out->h.al=mode;out->h.ah=cols;out->h.bh=page;break;
 case 2:assert(in->h.bh==page);row=in->h.dh;col=in->h.dl;assert(row<25 && col<cols);break;
 case 9:assert(in->h.bh==page);assert(col+in->x.cx<=cols);for(x=col;x<col+in->x.cx;++x){grid[row][x]=in->h.al;attrs[row][x]=in->h.bl;}break;
 case 6:assert(in->h.al==0);for(y=in->h.ch;y<=in->h.dh;++y)for(x=in->h.cl;x<=in->h.dl;++x){assert(y<25 && x<cols);grid[y][x]=' ';attrs[y][x]=in->h.bh;}break;
 case 3:assert(in->h.bh==page);out->h.ch=hidden?0x20:6;out->h.cl=7;break;
 case 1:assert(!(in->h.ch&0x20));hidden=0;break;
 default:assert(0);
 }
}
'''
main=r'''
int main(void)
{ unsigned m,p;int rc;const char *s="It's now safe to turn off your computer";
 for(m=0;m<8;++m)for(p=0;p<2;++p) {
  mode=m;cols=m<2?40:80;page=p;flags=0x80d3;ioerr=0;hidden=1;video_calls=0;
  memset(grid,'?',sizeof(grid));rc=night_draw();
  if(m<=3 || m==7) {
   assert(rc==1 && row==23 && col==0 && !hidden);
   if(cols==80)assert(memcmp(grid[17]+20,s,39)==0);
   else{assert(memcmp(grid[17]+7,"It's now safe to turn off",25)==0);assert(memcmp(grid[18]+13,"your computer",13)==0);}
   assert(grid[4][(cols-16*(cols==80?2:1))/2+6*(cols==80?2:1)]==176);assert(attrs[23][0]==7);
   if(cols==80){assert(grid[4][37]==176);assert(grid[8][26]==219 && grid[8][35]==219 && grid[8][36]==' ');}
   else assert(grid[8][13]==219 && grid[8][17]==219 && grid[8][18]==' ');
  } else assert(rc==0 && video_calls==1);
 }
 mode=3;cols=80;page=0;ioerr=0;
 for(m=0;m<4;++m) { flags=m==0?2:m==1?0x80c4:m==2?0x80c0:0x80d3;ioerr=m==3;video_calls=0;assert(night_draw()==0 && video_calls==0); }
 flags=0x80d3;ioerr=0;cols=132;video_calls=0;assert(night_draw()==0 && video_calls==1);
 puts("BIOS simulations: 10 supported mode/page draws; 6 graphics-mode rejects; 4 redirection/device/error rejects; unsupported-width reject.");return 0;
}
'''
(P/'NITESTUB.C').write_text(stub+block+main)
subprocess.run(['gcc','-x','c','-std=c89','-pedantic','-Wall','-Wextra','-Werror','-o',str(P/'NITESTUB'),str(P/'NITESTUB.C')],check=True)
r=subprocess.run([str(P/'NITESTUB')],capture_output=True,text=True,check=True)
# Exact transaction implementation unchanged apart from the presentation call.
old=(P/'BASESEL.C').read_text()
without=src.replace(src[src.index('/* Success presentation only.'):src.index('static void cleanup_restored(void)')],'')
without=without.replace('remove_snap(jrn,orig,on); restored_notice();','remove_snap(jrn,orig,on); puts("Original shell restored and reread verified.");')
without=without.replace("static int steps;\nstatic int show_night;", "static int steps;")
without=without.replace('else if(eqi(argv[1],"RECOVER")||eqi(argv[1],"FINISH")) { show_night=eqi(argv[1],"FINISH"); recover(); }','else if(eqi(argv[1],"RECOVER")) recover();')
without=without.replace('!eqi(argv[1],"RECOVER")&&!eqi(argv[1],"FINISH")&&!eqi(argv[1],"STATUS")','!eqi(argv[1],"RECOVER")&&!eqi(argv[1],"STATUS")').replace('SELECT|RECOVER|FINISH|STATUS','SELECT|RECOVER|STATUS')
assert without==old
oldbatch=(P/'BASESTRT.BAT').read_bytes()
assert (P/'TSTART.BAT').read_bytes()==oldbatch.replace((P/'OLDWIN.TXT').read_bytes(),(P/'NEWWIN.TXT').read_bytes())
assert [x for x in oldbatch.splitlines() if x.startswith(b'SET ')]==[x for x in (P/'TSTART.BAT').read_bytes().splitlines() if x.startswith(b'SET ')]
# Recovery-only text gate; stderr diagnostics and sidecar contents survive failures.
base=b'[boot]\r\nshell=PROGMAN.EXE\r\n[keyboard]\r\nkeep=1\r\n';msg=b"It's now safe to turn off your computer\n"
checks=[]
with tempfile.TemporaryDirectory(prefix='night-gate-') as td:
 q=Path(td);exe=P/'SHELLSEL'
 h=bytearray(192);h[:2]=b'MZ';h[60]=128;h[128:130]=b'NE';h[182]=2
 def reset():
  for f in q.iterdir():f.chmod(0o644);f.unlink()
  (q/'SYSTEM.INI').write_bytes(base);(q/'TSHELL.EXE').write_bytes(h);(q/'WIN.COM').write_bytes(b'\xeb\x09XWtest')
 def run(cmd,env=None):return subprocess.run([str(exe),cmd,str(q/'SYSTEM.INI')],env=dict(os.environ,**(env or {})),capture_output=True)
 reset();assert run('SELECT').returncode==0;x=run('RECOVER');assert x.returncode==0 and x.stdout==b'Original shell restored and reread verified.\n' and msg not in x.stdout;checks.append('ordinary RECOVER exact original success text')
 reset();x=run('FINISH');assert x.returncode==0 and x.stdout==b'No active shell selection; SYSTEM.INI unchanged.\n';checks.append('no-journal unchanged text')
 assert run('SELECT').returncode==0;x=run('FINISH');assert x.returncode==0 and x.stdout==msg and (q/'SYSTEM.INI').read_bytes()==base and not (q/'TSHELL.JRN').exists();checks.append('verified recovery exact plain text')
 x=run('FINISH');assert msg not in x.stdout;checks.append('idempotent no-journal no-success')
 for bad in ['foreign_journal','stale_temp','unexpected_shell','readonly_journal','duplicate_boot']:
  reset()
  if bad=='foreign_journal':(q/'TSHELL.JRN').write_bytes(b'foreign')
  elif bad=='stale_temp':(q/'TSHELL.NEW').write_bytes(b'stale')
  elif bad=='duplicate_boot':(q/'SYSTEM.INI').write_bytes(base+b'[boot]\r\nshell=OTHER.EXE\r\n')
  else:
   assert run('SELECT').returncode==0
   if bad=='unexpected_shell':(q/'SYSTEM.INI').write_bytes(base.replace(b'PROGMAN.EXE',b'OTHER.EXE'))
   else:(q/'TSHELL.JRN').chmod(0o444)
  x=run('FINISH');assert x.returncode!=0 and msg not in x.stdout and b'No unsafe fallback was attempted.' in x.stderr
  if bad in ['foreign_journal','unexpected_shell','readonly_journal']:assert (q/'TSHELL.JRN').exists()
  checks.append(bad+' diagnostic/no art')
 reset();assert run('SELECT').returncode==0;x=run('FINISH',{'TS_CRASH':'7'});assert x.returncode==99 and not x.stdout and not (q/'TSHELL.JRN').exists();checks.append('no pre-proof success at last crash checkpoint')
 reset();assert run('SELECT',{'TS_CRASH':'1'}).returncode==99;x=run('SELECT');assert x.returncode==0 and msg not in x.stdout and b'Original shell restored and reread verified.' in x.stdout and (q/'TSHELL.JRN').exists();checks.append('SELECT internal recovery stays plain')
results={'renderer':r.stdout.strip(),'transaction_source_identical':True,'batch_only_exact_post_win_block_changed':True,'configured_SET_lines_identical':True,'presentation_gate_checks':checks,'source_sha256':hashlib.sha256((P/'SHELLSEL.C').read_bytes()).hexdigest()}
(P/'TESTNITE.JSON').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results,indent=2))
