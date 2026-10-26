from pathlib import Path
import subprocess,sys,json
root=Path(__file__).resolve().parent;repo=root.parent/'oemdisplay-tandy'
common=['--windows',r'C:\Users\chad\Documents\Codex\2026-10-23\task-7\native\RLE-FOLLOWUP\AFTER-GUEST\BASEWINDOWS',
 '--reserve',str(repo/'src/tandysw/bin/RESERVE.COM'),'--probe',str(root/'RRSYNC1/RRBENCH.EXE'),
 '--dosbox',r'C:\DOSBox-X\dosbox-x.exe','--lease',r'C:\Users\chad\Documents\Codex\2026-10-06\tandy-emulator.lock']
drivers={'BASE':'XRBASE','OLD':'XRBATCH3','NEW':'XRSYNC2'}
for pan in ('x','y','z'):
 for variant in ('NEW','BASE','OLD'):
  out=root/('SAFE-'+variant+'-'+pan.upper())
  cmd=[sys.executable,str(repo/'src/rrect/RRXRUN.PY'),*common,'--driver',str(root/drivers[variant]/'HPXY.DRV'),
   '--out',str(out),'--pan',pan]
  if variant=='OLD':cmd+=['--expect-held']
  if pan=='y':cmd+=['--hardware']
  print('START',out.name,flush=True)
  with out.with_suffix('.txt').open('wb') as log:r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
  print('END',out.name,r.returncode,flush=True)
  if r.returncode:raise SystemExit(r.returncode)
  if variant=='BASE':
   ref=root/('SAFE-BASE-'+pan.upper());cand=root/('SAFE-NEW-'+pan.upper())
   cmd=[sys.executable,str(repo/'src/rrect/RRCMP.PY'),str(ref),str(cand),'--json',str(root/('SAFE-COMPARE-'+pan.upper()+'.json'))]
   with (root/('SAFE-COMPARE-'+pan.upper()+'.txt')).open('wb') as log:r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
   print('COMPARE',pan,r.returncode,flush=True)
   if r.returncode:raise SystemExit(r.returncode)
 ref=root/('SAFE-BASE-'+pan.upper());old=root/('SAFE-OLD-'+pan.upper())
 differences=[f.name for f in ref.glob('*.BIN') if f.read_bytes()!=(old/f.name).read_bytes()]
 assert sorted(differences)==['RB12.BIN','RM09.BIN'],differences
 print('OLD GAP CAUGHT',pan,differences,flush=True)
