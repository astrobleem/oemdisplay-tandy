/* Guest-side observer/controller for native Windows 3.0 Setup tests.
   Commands are fixture input in a preallocated 4 KB UITASK.TXT file.
   It never edits Windows configuration or installs a driver itself. */
#include <windows.h>
#include <stdlib.h>
#include <string.h>
#include <dos.h>
static HWND mainw;
static HINSTANCE instance;
static long last;
static char command[4097],buf[768];
static HFILE outf;
static void emit(LPSTR s){_lwrite(outf,s,lstrlen(s));_lwrite(outf,"\r\n",2);}
static void menus(HMENU m,int depth){int i,n,id;char s[160];HMENU sub;if(!m || depth>4)return;
 n=GetMenuItemCount(m);for(i=0;i<n;i++){id=GetMenuItemID(m,i);GetMenuString(m,i,s,sizeof(s),MF_BYPOSITION);wsprintf(buf,"MENU depth=%d pos=%d id=%d text=%s",depth,i,id,(LPSTR)s);emit(buf);sub=GetSubMenu(m,i);if(sub)menus(sub,depth+1);}}
static void windows(HWND w,int depth){char cls[64],txt[256];RECT r;HWND c;int i,n;DWORD style;
 while(w && depth<8){GetClassName(w,cls,sizeof(cls));GetWindowText(w,txt,sizeof(txt));GetWindowRect(w,&r);style=GetWindowLong(w,GWL_STYLE);
 wsprintf(buf,"WIN h=%u parent=%u id=%d vis=%d enabled=%d rect=%d,%d,%d,%d cls=%s text=%s",w,GetParent(w),GetDlgCtrlID(w),IsWindowVisible(w),IsWindowEnabled(w),r.left,r.top,r.right,r.bottom,(LPSTR)cls,(LPSTR)txt);emit(buf);
 if(!lstrcmpi(cls,"ListBox") || !lstrcmpi(cls,"ComboBox")){int combo=!lstrcmpi(cls,"ComboBox");n=(int)SendMessage(w,combo?CB_GETCOUNT:LB_GETCOUNT,0,0L);wsprintf(buf,"ITEMS h=%u count=%d selected=%d",w,n,(int)SendMessage(w,combo?CB_GETCURSEL:LB_GETCURSEL,0,0L));emit(buf);
 for(i=0;i<n && i<64;i++){txt[0]=0;SendMessage(w,combo?CB_GETLBTEXT:LB_GETTEXT,i,(LONG)(LPSTR)txt);wsprintf(buf,"ITEM h=%u i=%d text=%s",w,i,(LPSTR)txt);emit(buf);}}
 if(depth==0)menus(GetMenu(w),0);c=GetWindow(w,GW_CHILD);if(c)windows(c,depth+1);w=GetWindow(w,GW_HWNDNEXT);}}
static void snapshot(void){HDC dc;int q=-1,o[3]={-2,0,0};char load[256];WORD seg;HFILE f;
 outf=_lcreat("C:\\UISTATE.TXT",0);if(outf==HFILE_ERROR)return;
 dc=GetDC(NULL);Escape(dc,0x5850,2,(LPSTR)&q,(LPSTR)o);GetProfileString("windows","load","",load,sizeof(load));
 wsprintf(buf,"STATE seq=%ld width=%d height=%d top=%d free=%lu helper=%u active=%u focus=%u load=%s",last,GetDeviceCaps(dc,HORZRES),GetDeviceCaps(dc,VERTRES),o[0],GetFreeSpace(0),FindWindow("XTPan",NULL),GetActiveWindow(),GetFocus(),(LPSTR)load);emit(buf);ReleaseDC(NULL,dc);
 windows(GetWindow(GetDesktopWindow(),GW_CHILD),0);_lclose(outf);
 seg=GetPrivateProfileInt("test","vseg",0,"C:\\SPTEST.INI");if(!seg)seg=(WORD)((*(BYTE FAR *)0x0040008aL & 6)<<10);
 f=_lcreat("C:\\UIVRAM.BIN",0);if(f!=HFILE_ERROR){_lwrite(f,(void FAR *)((DWORD)seg<<16),32768U);_lclose(f);} {union REGS a,b;a.h.ah=0x0d;intdos(&a,&b);}}
static void memory(char *label){HFILE f;char s[160];f=_lopen("C:\\UIMEM.LOG",OF_WRITE);if(f==HFILE_ERROR)f=_lcreat("C:\\UIMEM.LOG",0);_llseek(f,0L,2);wsprintf(s,"%s=%lu\r\n",(LPSTR)label,GetFreeSpace(0));_lwrite(f,s,lstrlen(s));_lclose(f);}
static void brush(void){HBRUSH b[16];HDC dc;RECT r;int i,k,ok=0;HFILE f;char s[80];
 memory("BRUSH_BEFORE");dc=GetDC(NULL);r.left=0;r.top=0;r.right=1;r.bottom=1;
 for(i=0;i<16;i++){b[i]=CreateSolidBrush(RGB((i&1)?255:0,(i&2)?255:0,(i&4)?255:0));FillRect(dc,&r,b[i]);}memory("BRUSH_ALLOCATED");
 for(i=0;i<16;i++)ok+=DeleteObject(b[i])!=0;memory("BRUSH_DELETED");
 for(k=0;k<10;k++){for(i=0;i<16;i++){b[i]=CreateSolidBrush(RGB(i*16,0,0));FillRect(dc,&r,b[i]);}for(i=0;i<16;i++)ok+=DeleteObject(b[i])!=0;}
 ReleaseDC(NULL,dc);memory("BRUSH_AFTER_10_CYCLES");f=_lopen("C:\\UIMEM.LOG",OF_WRITE);_llseek(f,0L,2);wsprintf(s,"DELETE_SUCCESS=%d\r\n",ok);_lwrite(f,s,lstrlen(s));_lclose(f);}
static void action(void){HFILE f;UINT n;char *seq,*op,*a,*b;HWND w,p;int id,combo,index;char cls[64];
 f=_lopen("C:\\UITASK.TXT",OF_READ);if(f==HFILE_ERROR)return;n=_lread(f,command,4096);_lclose(f);command[n]=0;
 seq=strtok(command," \r\n");if(!seq || atol(seq)<=last)return;last=atol(seq);op=strtok(NULL," \r\n");if(!op)return;
 if(!strcmp(op,"RUN")){a=strtok(NULL,"\r\n");if(a)WinExec(a,SW_SHOWNORMAL);}
 else if(!strcmp(op,"MEM")){a=strtok(NULL," \r\n");memory(a?a:"MEM");}
 else if(!strcmp(op,"BRUSH"))brush();
 else if(!strcmp(op,"EXIT"))ExitWindows(0,0);
 else if(!strcmp(op,"SELECT")){a=strtok(NULL," \r\n");b=strtok(NULL," \r\n");if(a && b){w=(HWND)atoi(a);index=atoi(b);GetClassName(w,cls,sizeof(cls));combo=!lstrcmpi(cls,"ComboBox");SendMessage(w,combo?CB_SETCURSEL:LB_SETCURSEL,index,0L);p=GetParent(w);id=GetDlgCtrlID(w);PostMessage(p,WM_COMMAND,id,MAKELONG(w,combo?CBN_SELCHANGE:LBN_SELCHANGE));}}
 else if(!strcmp(op,"TEXT")){a=strtok(NULL," \r\n");b=strtok(NULL,"\r\n");if(a && b)SendMessage((HWND)atoi(a),WM_SETTEXT,0,(LONG)(LPSTR)b);}
 else if(!strcmp(op,"CLICK")){a=strtok(NULL," \r\n");if(a){w=(HWND)atoi(a);PostMessage(GetParent(w),WM_COMMAND,GetDlgCtrlID(w),MAKELONG(w,BN_CLICKED));}}
 else if(!strcmp(op,"MENU")){a=strtok(NULL," \r\n");b=strtok(NULL," \r\n");if(a && b)PostMessage((HWND)atoi(a),WM_COMMAND,atoi(b),0L);}
 else if(!strcmp(op,"CLOSE")){a=strtok(NULL," \r\n");if(a)PostMessage((HWND)atoi(a),WM_CLOSE,0,0L);}
 snapshot();}
long FAR PASCAL WndProc(HWND w,unsigned m,WORD p,LONG l){if(m==WM_TIMER){action();snapshot();return 0;}if(m==WM_DESTROY){KillTimer(w,1);PostQuitMessage(0);return 0;}return DefWindowProc(w,m,p,l);}
int PASCAL WinMain(HINSTANCE i,HINSTANCE prev,LPSTR cmd,int show){WNDCLASS wc;MSG msg;instance=i;memory("UITEST_ENTRY");
 wc.style=0;wc.lpfnWndProc=WndProc;wc.cbClsExtra=wc.cbWndExtra=0;wc.hInstance=i;wc.hIcon=NULL;wc.hCursor=NULL;wc.hbrBackground=NULL;wc.lpszMenuName=NULL;wc.lpszClassName="UIObserver";
 if(!RegisterClass(&wc))return 1;mainw=CreateWindow("UIObserver","UI observer",WS_POPUP,0,0,0,0,NULL,NULL,i,NULL);if(!mainw)return 2;SetTimer(mainw,1,500,NULL);memory("UITEST_TIMER");
 while(GetMessage(&msg,NULL,0,0)){TranslateMessage(&msg);DispatchMessage(&msg);}return 0;}
