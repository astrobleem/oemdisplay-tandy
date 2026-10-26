from pathlib import Path
import os,shutil,subprocess
HERE=Path(__file__).resolve().parent
OUT=HERE.parents[1].parent/'tandy-pan-integration/app-build-03'
OUT.mkdir();shutil.copyfile(HERE/'APPQA.C',OUT/'APPQA.C')
(OUT/'APPQA.LNK').write_text('system windows\nname APPQA.EXE\noption map=APPQA.MAP\nfile APPQA.obj\n')
env=dict(os.environ,WATCOM=r'C:\WATCOM',INCLUDE=r'C:\WATCOM\H;C:\WATCOM\H\WIN')
with (OUT/'BUILD.LOG').open('wb') as log:
    for cmd in [[r'C:\WATCOM\BINNT\WCC.EXE','-zW','-0','-ms','-od','-we',r'-i=C:\WATCOM\H',r'-i=C:\WATCOM\H\WIN','APPQA.C'],[r'C:\WATCOM\BINNT\WLINK.EXE','@APPQA.LNK']]:
        subprocess.run(cmd,cwd=OUT,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
print('Built',OUT/'APPQA.EXE')
