"""Prepare a private native placement test using the existing UITEST observer.

No emulator or guest image is started or changed. The generated test client
adds bounded placement/workspace commands for ordinary Windows applications.
Internal USER calls are probes only, never enabled in the placement service.
"""
from pathlib import Path
import argparse,hashlib,json,shutil
here=Path(__file__).resolve().parent
repo=here.parents[1]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--out',type=Path,required=True)
p.add_argument('--placement',type=Path,required=True)
p.add_argument('--trace',action='store_true',help='private diagnosis only; never qualifies a helper')
args=p.parse_args();out=args.out.resolve();out.mkdir(parents=True,exist_ok=False)
def write(name,s):
    (out/name).write_bytes(s.replace('\r\n','\n').replace('\n','\r\n').encode('ascii'))
source=(repo/'src/softpan/UITEST.C').read_text()
source=source.replace('#include <windows.h>','#include <windows.h>\n#include "WDWIN.H"\n#include "WTPLACE.H"',1)
extra=r'''
/* The probe ABI is corroborated by Wine's historical USER spec (460/461),
 * not assumed from a later WINDOWPLACEMENT structure. Native results must
 * establish this exact real-mode USER implementation before production use. */
typedef UINT (FAR PASCAL *IPGET)(HWND,LPRECT,LPPOINT);
typedef void (FAR PASCAL *IPSET)(HWND,UINT,LPRECT,LPPOINT);
static void qlog(LPSTR text) {
 HFILE f;f=_lopen("C:\\WTPLACE.LOG",OF_WRITE);
 if(f==HFILE_ERROR)f=_lcreat("C:\\WTPLACE.LOG",0);
 if(f==HFILE_ERROR)return;_llseek(f,0L,2);_lwrite(f,text,lstrlen(text));
 _lwrite(f,"\r\n",2);_lclose(f);
}
static void placement(HWND w) {
 WTPLACEMENT p;int code;HWND active,previous;
 active=GetActiveWindow();previous=GetWindow(w,GW_HWNDPREV);
 code=WTPlaceInit(w,&p);if(!code)code=WTPlaceGet(w,&p);
 wsprintf(buf,"PLACE h=%u code=%d state=%u known=%u normal=%d,%d,%d,%d active=%u,%u previous=%u,%u size=%u",
  w,code,p.state,p.flags,p.normal.left,p.normal.top,p.normal.right,p.normal.bottom,
  active,GetActiveWindow(),previous,GetWindow(w,GW_HWNDPREV),p.size);qlog(buf);
}
static void internal(HWND w,int set,UINT show,RECT *want) {
 struct {WORD first;RECT normal;POINT icon;WORD last;} data;
 IPGET get;IPSET put;UINT state;HWND active,previous;
 data.first=0x1234;data.last=0x5678;
 data.normal.left=data.normal.top=data.normal.right=data.normal.bottom=-12000;
 data.icon.x=data.icon.y=-12000;
 get=(IPGET)GetProcAddress(GetModuleHandle("USER"),(LPSTR)460L);
 put=(IPSET)GetProcAddress(GetModuleHandle("USER"),(LPSTR)461L);
 active=GetActiveWindow();previous=GetWindow(w,GW_HWNDPREV);
 if(!get || (set && !put)){qlog("INTERNAL unavailable");return;}
 if(set){qlog("INTSET_BEGIN");put(w,show,want,NULL);}
 state=get(w,&data.normal,&data.icon);
 wsprintf(buf,"INTERNAL h=%u set=%d show=%u result=%u normal=%d,%d,%d,%d icon=%d,%d guard=%d active=%u,%u previous=%u,%u iconic=%d zoomed=%d",
  w,set,show,state,data.normal.left,data.normal.top,data.normal.right,data.normal.bottom,
  data.icon.x,data.icon.y,data.first==0x1234 && data.last==0x5678,active,GetActiveWindow(),previous,GetWindow(w,GW_HWNDPREV),IsIconic(w),IsZoomed(w));qlog(buf);
}
'''
source=source.replace('static void action(void)',extra+'\nstatic void action(void)',1)
anchor=' if(!strcmp(op,"RUN"))'
actions=r'''
 if(!strcmp(op,"WDINIT")){int r; r=WDWinInit(2048,2048);WDWinExclude("Progman");wsprintf(buf,"WDINIT %d",r);qlog(buf);}
 else if(!strcmp(op,"WDPAN")){int r,x=0,y=0;a=strtok(NULL," \r\n");b=strtok(NULL," \r\n");r=(a && b)?WDWinPan(atoi(a),atoi(b)):WD_E_RANGE;WDWinViewport(&x,&y);wsprintf(buf,"WDPAN r=%d x=%d y=%d dropped=%u",r,x,y,WDWinDropped());qlog(buf);}
 else if(!strcmp(op,"WDHOME")){int r;r=WDWinHome();wsprintf(buf,"WDHOME %d",r);qlog(buf);}
 else if(!strcmp(op,"WDOFF")){int r;r=WDWinShutdown();wsprintf(buf,"WDOFF %d",r);qlog(buf);}
 else if(!strcmp(op,"WTGET")){a=strtok(NULL," \r\n");if(a)placement((HWND)atoi(a));}
 else if(!strcmp(op,"INTGET")){a=strtok(NULL," \r\n");if(a)internal((HWND)atoi(a),0,0,NULL);}
 else if(!strcmp(op,"INTSET")){RECT r;char *v[6];int j;for(j=0;j<6;j++)v[j]=strtok(NULL," \r\n");if(v[5]){r.left=atoi(v[2]);r.top=atoi(v[3]);r.right=r.left+atoi(v[4]);r.bottom=r.top+atoi(v[5]);internal((HWND)atoi(v[0]),1,atoi(v[1]),&r);}}
 else if(!strcmp(op,"SHOW")){a=strtok(NULL," \r\n");b=strtok(NULL," \r\n");if(a && b)ShowWindow((HWND)atoi(a),atoi(b));}
 else if(!strcmp(op,"SYSCOMMAND")){a=strtok(NULL," \r\n");b=strtok(NULL," \r\n");if(a && b)PostMessage((HWND)atoi(a),WM_SYSCOMMAND,atoi(b),0L);}
 else if(!strcmp(op,"MOVE")){char *x,*y;a=strtok(NULL," \r\n");x=strtok(NULL," \r\n");y=strtok(NULL," \r\n");if(a && x && y)SetWindowPos((HWND)atoi(a),0,atoi(x),atoi(y),0,0,SWP_NOSIZE|SWP_NOZORDER|SWP_NOACTIVATE);}
 else if(!strcmp(op,"POINTER")){a=strtok(NULL," \r\n");b=strtok(NULL," \r\n");if(a && b)SetCursorPos(atoi(a),atoi(b));}
 else if(!strcmp(op,"ACTIVATE")){a=strtok(NULL," \r\n");if(a)SetActiveWindow((HWND)atoi(a));}
 else
'''
assert source.count(anchor)==1
source=source.replace(anchor,actions+anchor,1)
anchor=' if(!lstrcmpi(cls,"Static"))'
assert source.count(anchor)==1
source=source.replace(anchor,' wsprintf(buf,"WINDOW_STATE h=%u owner=%u style=%lx iconic=%d zoomed=%d",w,GetWindow(w,GW_OWNER),style,IsIconic(w),IsZoomed(w));emit(buf);\n'+anchor,1)
write('WDQA.C',source)
write('WDQA.DEF',(repo/'src/softpan/UITEST.DEF').read_text().replace('UITEST','WDQA'))
write('WDQA.RSP','WDQA.OBJ+WDCORE.OBJ+WDWIN.OBJ+WTPLACE.OBJ\nWDQA.EXE\nWDQA.MAP\nC:\\LIB\\SLIBCEW.LIB C:\\LIB\\LIBW.LIB\nWDQA.DEF\n')
files=[here/n for n in ('WDCORE.C','WDCORE.H','WDWIN.C','WDWIN.H')]
files += [args.placement/n for n in ('WTPLACE.C','WTPLACE.H')]
for f in files:shutil.copyfile(f,out/f.name)
if args.trace:
    # Test-only call-site tracing uses the same existing Win16 file APIs as
    # UITEST. Generated copies are hashed and explicitly excluded from runtime
    # qualification; production sources and package pins are not modified.
    trace=r'''
static void wtp_trace(LPCSTR stage,HWND w,RECT FAR *want,WTPLACEMENT FAR *p,
                     WORD state,int visible,HWND active,HWND previous) {
 char b[384];HFILE f;
 wsprintf(b,"WTP %s h=%u want=%d,%d,%d,%d actual=%d,%d,%d,%d state=%u,%u flags=%u visible=%d,%d active=%u,%u previous=%u,%u direct=%u validprev=%d\r\n",
 stage,w,want->left,want->top,want->right,want->bottom,
 p->normal.left,p->normal.top,p->normal.right,p->normal.bottom,state,p->state,p->flags,
 visible,IsWindowVisible(w),active,GetActiveWindow(),previous,wtp_previous(w),
 GetWindow(w,GW_HWNDPREV),!previous || IsWindow(previous));
 f=_lopen("C:\\WTPTRACE.LOG",OF_WRITE);if(f==HFILE_ERROR)f=_lcreat("C:\\WTPTRACE.LOG",0);
 if(f!=HFILE_ERROR){_llseek(f,0L,2);_lwrite(f,b,lstrlen(b));_lclose(f);}
}
'''
    s=(out/'WTPLACE.C').read_text()
    s=s.replace('int FAR PASCAL WTPlaceAvailable(void)',trace+'\nint FAR PASCAL WTPlaceAvailable(void)',1)
    s=s.replace('        put(window, visible ? SW_SHOWNA : SW_HIDE, &wanted, 0);',
        '        wtp_trace("BEFORE",window,&wanted,p,state,visible,active,previous);\n'
        '        put(window, visible ? SW_SHOWNA : SW_HIDE, &wanted, 0);',1)
    s=s.replace('        if (wtp_previous(window) != previous) {',
        '        wtp_trace("AFTER",window,&wanted,p,state,visible,active,previous);\n'
        '        if (wtp_previous(window) != previous) {\n'
        '            wtp_trace("FIX_BEGIN",window,&wanted,p,state,visible,active,previous);',1)
    s=s.replace('        return p->state == state && (p->flags & WTP_SAVED) &&',
        '        wtp_trace("FINAL",window,&wanted,p,state,visible,active,previous);\n'
        '        return p->state == state && (p->flags & WTP_SAVED) &&',1)
    write('WTPLACE.C',s)
    trace=r'''
static void wdw_trace(WDMOVE *m,WTPLACEMENT *p,int ok) {
 char b[256];HFILE f;
 wsprintf(b,"APPLY_FAIL h=%u want=%d,%d actual=%d,%d,%d,%d state=%u flags=%u ok=%d\r\n",
 m->hwnd,m->x,m->y,p->normal.left,p->normal.top,p->normal.right,p->normal.bottom,p->state,p->flags,ok);
 f=_lopen("C:\\WTPTRACE.LOG",OF_WRITE);if(f==HFILE_ERROR)f=_lcreat("C:\\WTPTRACE.LOG",0);
 if(f!=HFILE_ERROR){_llseek(f,0L,2);_lwrite(f,b,lstrlen(b));_lclose(f);}
}
'''
    s=(out/'WDWIN.C').read_text().replace('static WD wdw_wd;',trace+'\nstatic WD wdw_wd;',1)
    s=s.replace('            failed = 1;','            wdw_trace(m,&place,ok);\n            failed = 1;',1)
    write('WDWIN.C',s)
# Compile the actual existing helper with the same placement source. The
# generated QA client still owns no background workspace until WDINIT.
for n in ('XTPAN.C','XTPAN.DEF','XTPAN.RSP'):
    shutil.copyfile(repo/'src/xtpan'/n,out/n)
for n in ('PANSET.C','PANSET.H','PANDLG.C','PANDLG.H'):
    shutil.copyfile(repo/'src/panui'/n,out/n)
bat='@ECHO OFF\nPATH=C:\\BIN\nSET INCLUDE=C:\\DDK\\286\\INC;C:\\INCLUDE\nSET LIB=C:\\LIB\n'
for i,n in enumerate(('WDQA','WDCORE','WDWIN','WTPLACE')):
    bat+='CL /nologo /c /G0 /Gw /AS /W3 /Od '+n+'.C '+('>' if not i else '>>')+' BUILD.LOG\nIF ERRORLEVEL 1 GOTO FAIL\n'
bat+='LINK4 /NOE /NOD @WDQA.RSP >> BUILD.LOG\nIF ERRORLEVEL 1 GOTO FAIL\n'
for n in ('XTPAN','PANSET','PANDLG'):
    bat+='CL /nologo /c /G0 /Gw /AS /W3 /Od '+n+'.C >> BUILD.LOG\nIF ERRORLEVEL 1 GOTO FAIL\n'
bat+='LINK4 /NOE /NOD @XTPAN.RSP >> BUILD.LOG\nIF ERRORLEVEL 1 GOTO FAIL\nECHO PASS >> BUILD.LOG\nGOTO END\n:FAIL\nECHO FAIL >> BUILD.LOG\n:END\nEXIT\n'
write('BUILDQA.BAT',bat)
record={'status':'PREPARED_NOT_RUN','client':'existing src/softpan/UITEST.C with bounded placement commands',
        'instrumented_diagnosis_only':args.trace,
        'internal_calls':'test-only USER460/461 probes, not enabled in production service',
        'sources':{f.name:{'bytes':len(f.read_bytes()),'sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
                   for f in out.iterdir() if f.is_file()}}
write('PREPARE.JSN',json.dumps(record,indent=2)+'\n')
print('Prepared native client and MSC6 recipe:',out)
