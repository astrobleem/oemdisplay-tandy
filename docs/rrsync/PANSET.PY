from pathlib import Path
import subprocess,sys,json
root=Path(__file__).resolve().parent;repo=root.parent/'oemdisplay-tandy'
common=['--windows',r'C:\Users\chad\Documents\Codex\2026-10-23\task-7\native\RLE-FOLLOWUP\AFTER-GUEST\BASEWINDOWS',
 '--reserve',str(repo/'src/tandysw/bin/RESERVE.COM'),'--probe',str(root/'RRSYNC2/RRBENCH.EXE'),
 '--dosbox',r'C:\DOSBox-X\dosbox-x.exe','--lease',r'C:\Users\chad\Documents\Codex\2026-10-06\tandy-emulator.lock','--pan-only']
drivers={'BASE':root/'XRBASE/HPXY.DRV','OLD':root/'XRBATCH3/HPXY.DRV','NEW':root/'SYNC-OEM/XRSYNC.DRV'}
for pan in ('x','y','z'):
 for v in ('BASE','OLD','NEW'):
  out=root/f'PAN-{v}-{pan.upper()}'
  cmd=[sys.executable,str(repo/'src/rrect/RRXRUN.PY'),*common,'--driver',str(drivers[v]),'--out',str(out),'--pan',pan]
  if v=='NEW':cmd+=['--driver-name','XRSYNC.DRV']
  if pan=='y':cmd+=['--hardware']
  print('START',out.name,flush=True)
  with out.with_suffix('.txt').open('wb') as log:r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
  print('END',out.name,r.returncode,flush=True)
  if r.returncode:raise SystemExit(r.returncode)
 for v in ('OLD','NEW'):
  cmd=[sys.executable,str(repo/'src/rrect/RRCMP.PY'),str(root/f'PAN-BASE-{pan.upper()}'),str(root/f'PAN-{v}-{pan.upper()}'),
       '--json',str(root/f'PAN-COMPARE-{v}-{pan.upper()}.json')]
  with (root/f'PAN-COMPARE-{v}-{pan.upper()}.txt').open('wb') as log:r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
  print('COMPARE',v,pan,r.returncode,flush=True)
  if r.returncode:raise SystemExit(r.returncode)
