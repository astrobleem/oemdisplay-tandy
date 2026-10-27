"""Build/finalize the staged CGA transaction using its exact checked inventory."""
from pathlib import Path
import argparse,importlib.machinery,sys
import PREPARE as P
import CGASTAGE
ROOT=Path(__file__).resolve().parents[2]
base=P.base('CGA.ZIP');m=CGASTAGE.module({n[4:]:b for n,b in base.items() if n.startswith('CGA/')});sys.modules['PACKCGA']=m
if len(sys.argv)>1 and sys.argv[1]=='finish':
 p=argparse.ArgumentParser()
 for n in ('prepared','build','out'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args(sys.argv[2:]);m.finish(a.prepared,a.build,a.out)
else:
 b=importlib.machinery.SourceFileLoader('pan_cga_native_build',str(ROOT/'src/cga/BUILDSET.PY')).load_module();b.main()
