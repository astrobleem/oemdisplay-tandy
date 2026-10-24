from pathlib import Path
import json,subprocess,sys,importlib.machinery
root=Path(__file__).resolve().parent;repo=root.parent/'oemdisplay-tandy'
checker=importlib.machinery.SourceFileLoader('rlecheck',str(repo/'src/tandysw/MODECHK.PY')).load_module()
home=dict(checker.PROFILES['640x256x16-rle-pan']);home.pop('rle_pan')
checker.PROFILES['640x256x16-home']=home
for phase in (32,64):
 for v in ('BASE','OLD','NEW'):
  out=root/f'SRLE{phase}-{v}'
  cmd=[sys.executable,str(root/'OWNED.PY'),'--report',str(out/'LEASE.json'),r'C:\DOSBox-X\dosbox-x.exe','-nopromptfolder','-conf',str(out/'RUN.CNF')]
  with (out/'RUNNER.txt').open('wb') as log:r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
  if r.returncode:raise SystemExit(r.returncode)
  report=checker.analyze(out/'CROOT','640x256x16-rle-pan' if phase==32 else '640x256x16-home',phase)
  (out/'MODECHK.json').write_text(json.dumps(report,indent=2)+'\n')
  print(out.name,report['pass'],report['case_count'],report['pixels_compared'],flush=True)
  assert report['pass'],[(x.get('name'),x) for x in report.get('assertions',[]) if not x['pass']]
