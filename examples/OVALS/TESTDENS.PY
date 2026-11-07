"""Detect stale dense history and history-dependent motion cadence regressions."""
from pathlib import Path
import argparse,json,re,runpy,subprocess,tempfile
HERE=Path(__file__).resolve().parent
def check():
 source=(HERE/'ORBITS.C').read_text();draw=source[source.index('static int rotatedOval'):source.index('/* Destroying the GDI popup')]
 if re.search(r'\b(?:MoveTo|LineTo|Rectangle|Polygon|TextOut|SetPixel)\s*\(',draw):raise ValueError('Non-oval artwork API introduced')
 if draw.count('Ellipse(')!=1 or draw.count('Polyline(')!=1 or 'fxVertex(p,n,&x,&y)' not in draw:raise ValueError('Exact oval primitive/vertex route required')
 edits=[('stale-history','slotCount=fxCount(activeEffect,starCount);clearRow=stripe=0;\n   for(n=0;n<MAXSTARS;n++)stars[n].visible=0;','slotCount=fxCount(activeEffect,starCount);clearRow=stripe=0;\n   for(n=0;n<starCount;n++)stars[n].visible=0;','memcmp(actual,want'),('history-cadence','if(!(totalCells&(unsigned long)(starCount-1)))','if(!stripe)','frames==totalCells')]
 detected=[]
 with tempfile.TemporaryDirectory() as td:
  root=Path(td);(root/'OVALFX.H').write_bytes((HERE/'OVALFX.H').read_bytes())
  for name,old,new,expected in edits:
   if source.count(old)!=1:raise ValueError('Mutation anchor missing: '+name)
   (root/'ORBITS.C').write_text(source.replace(old,new));module=runpy.run_path(str(HERE/'TESTFX.PY'));fn=module['check'];fn.__globals__['HERE']=root
   try:fn()
   except ValueError as e:
    if expected not in str(e):raise ValueError('Unexpected mutation failure: '+str(e))
    detected.append(name)
   else:raise AssertionError('Dense-state mutation escaped: '+name)
 return {'pass':True,'mutations_detected':detected,'all_oval_source_route':'Ellipse or fxVertex-generated33-point closed Polyline only; PatBlt clears background','scope':'host sparse XOR/clock stubs and source checks; NOT native raster or timing'}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--report',type=Path,required=True);a=p.parse_args();d=check();a.report.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(d,indent=2))
