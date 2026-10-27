"""Stage the existing CGA transaction with one public PAN entry and exact inventories."""
from pathlib import Path
import hashlib,sys,types
ROOT=Path(__file__).resolve().parents[2]
def module(baseline):
 sys.path.insert(0,str(ROOT/'src/cga'))
 path=ROOT/'src/cga/PACKCGA.PY';s=path.read_text()
 s=s.replace("'PANCFG.EXE','XTPAN.EXE'}", "'PAN.EXE','XYCTL.EXE','PANCFG.EXE','XTPAN.EXE'}",1)
 s=s.replace("HELPERS={'CGACTL.EXE','PANCTL.EXE','PANCFG.EXE','XTPAN.EXE'}", "HELPERS={'CGACTL.EXE','PANCTL.EXE','PANCFG.EXE','XTPAN.EXE','PAN.EXE','XYCTL.EXE'}")
 s=s.replace("set(pin)-set(oldpin)!={'PANCFG.EXE','XTPAN.EXE'}", "set(pin)-set(oldpin)!={'PAN.EXE','XYCTL.EXE'}")
 s=s.replace("list(pin).index('PANCFG.EXE')", "list(pin).index('PAN.EXE')").replace("list(pin).index('XTPAN.EXE')", "list(pin).index('XYCTL.EXE')")
 s=s.replace("helper_by_mode={'100':'CGACTL.EXE','320':'CGACTL.EXE','640':'CGACTL.EXE','PAN':'PANCTL.EXE'}","helper_by_mode={'100':'PAN.EXE','320':'CGACTL.EXE','640':'CGACTL.EXE','PAN':'PAN.EXE'}")
 s=s.replace("readme=(HERE/'README.TXT').read_bytes()", "readme=(repo/'tools/PAN/GUIDES/CGA.TXT').read_bytes()")
 m=types.ModuleType('pan_cga_recipe');m.__file__=str(path);exec(compile(s,str(path),'exec'),m.__dict__)
 m.ROOT_CGA_BASE=lambda repo:baseline
 original=m.CGASET.stage
 def stage(repo,out,header):
  original(repo,out,header);p=out/'SETUP.C';s=p.read_text()
  a='!strcmp(cga_files[i].target,"XTPAN.EXE"))'
  assert s.count(a)==1;s=s.replace(a,'!strcmp(cga_files[i].target,"XTPAN.EXE") || !strcmp(cga_files[i].target,"PAN.EXE") || !strcmp(cga_files[i].target,"XYCTL.EXE"))')
  a='args[4]=pan ? "PANCTL.EXE" : "CGACTL.EXE";'
  assert s.count(a)==1;s=s.replace(a,'args[4]=(!cga_legacy && (pan || cga_small)) ? "PAN.EXE" : pan ? "PANCTL.EXE" : "CGACTL.EXE";')
  p.write_bytes(s.replace('\n','\r\n').encode())
  return {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()}
 m.CGASET.stage=stage
 return m
