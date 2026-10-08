from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
root=here.parent
source=(root/'PROGMENU.C').read_text()
a=source.index('static void pmbundles(void)')
b=source.index('static int pmopen(',a)
fixture=(here/'BUNDLE.C').read_text().replace('/* PRODUCTION */',source[a:b])
with tempfile.TemporaryDirectory(prefix='bundle-test-') as td:
 p=Path(td);c=p/'BUNDLE.C';exe=p/'BUNDLE.EXE'
 c.write_text(fixture)
 subprocess.run(['gcc','-x','c','-std=c89','-Wall','-Wextra','-Werror','-I',str(root),str(c),str(root/'GRPREAD.C'),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
