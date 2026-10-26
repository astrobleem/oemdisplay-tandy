from pathlib import Path
import subprocess,os,shutil
HERE=Path(__file__).resolve().parent
OUT=HERE.parents[1].parent/'tandy-pan-integration/qa-build-04'
OUT.mkdir();shutil.copyfile(HERE/'PANQA.C',OUT/'PANQA.C')
(OUT/'PANQA.LNK').write_text('system windows\nname PANQA.EXE\noption map=PANQA.MAP\nfile PANQA.obj\n')
env=dict(os.environ,WATCOM=r'C:\WATCOM',INCLUDE=r'C:\WATCOM\H;C:\WATCOM\H\WIN')
with (OUT/'BUILD.LOG').open('wb') as log:
 for cmd in [[r'C:\WATCOM\BINNT\WCC.EXE','-zW','-0','-ms','-od','-we',r'-i=C:\WATCOM\H',r'-i=C:\WATCOM\H\WIN','PANQA.C'],
             [r'C:\WATCOM\BINNT\WLINK.EXE','@PANQA.LNK']]:
  subprocess.run(cmd,cwd=OUT,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
print('Built',OUT/'PANQA.EXE')
