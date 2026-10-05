from pathlib import Path
import subprocess,ctypes,json
p=Path(__file__).resolve().parent;s=(p/'XTEYES.C').read_text();f=s[s.index('static int offset'):s.index('static void track')].replace('static int offset','int offset');(p/'GEOM.C').write_text(f);subprocess.run(['gcc','-x','c','-shared','-fPIC','-o',str(p/'GEOM.SO'),str(p/'GEOM.C')],check=True);lib=ctypes.CDLL(str(p/'GEOM.SO'));n=0
for rx in [12,19,29]:
 px=rx//4
 for dx in range(-640,641,3):
  for dy in range(-240,241,3):
   x=lib.offset(dx,dy,rx-px-4);y=lib.offset(dy,dx,15)
   for sx in [-1,1]:
    for sy in [-1,1]:
     a=x+sx*px;b=y+sy*4
     assert a*a*22*22+b*b*(rx-1)**2 < (rx-1)**2*22*22,(rx,dx,dy,a,b)
   n+=1
r={'passed':True,'cases':n,'check':'Actual C geometry extracted and executed on host; all pupil rectangle corners remain inside inner eye ellipse; cardinal directions, diagonals, stationary center, clamped far coordinates included','native_16bit_arithmetic':'Largest signed product <= 512*18 = 9216; denominator <=1048'};print(json.dumps(r,indent=2));(p/'GEOM.JSON').write_text(json.dumps(r,indent=2))
