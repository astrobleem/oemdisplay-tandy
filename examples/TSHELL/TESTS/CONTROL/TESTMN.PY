from pathlib import Path
import os,re,subprocess,tempfile
r=Path(__file__).resolve().parent
source=(r/'../../TSHELL.C').resolve().read_text()
def block(start,end):return source[source.index(start):source.index(end)]
production=block('static int popupheight(', 'static void clockpopup(')
defines='\n'.join(x for x in source.splitlines() if re.match(r'#define (MYCOMPUTER|PROGRAMS|RUNAPP|SYSTEMMENU|SETTINGSMENU|ABOUTSYS|SAVERSETUP|FIRSTAPP|CLOSEAPP|EXITWIN|OPENSYSTEM) ',x))+'\n#define CP_OPEN 59\n#define CP_FIRST 60\n'
dispatch=block(' case OPENSYSTEM:', ' case WM_LBUTTONDBLCLK:')+' case WM_COMMAND:\n'+block('  if(wp==START)', '  TandyHoldAction();').replace('  if(wp==START){popup(w);return 0;}\n','')
# Production handlers return a Win16 result; fixture dispatch must match.
text=(r/'MNTEST.C').read_text().replace('static void dispatch','static int dispatch').replace(' default:break;}}',' default:break;}return 0;}')
text=text.replace('/* DEFINES */',defines).replace('/* PRODUCTION */',production).replace('/* DISPATCH */',dispatch)
with tempfile.TemporaryDirectory(prefix='tsmenu-') as tmp:
 c=Path(tmp)/'MNTEST.C';exe=Path(tmp)/'MNTEST.EXE';c.write_text(text)
 subprocess.run([os.environ.get('CC','gcc'),'-x','c','-std=c89','-Wall','-Wextra','-Werror',str(c),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
