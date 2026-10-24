/* Original, opt-in Windows 3.0 real-mode focus reveal helper.
 * No hooks, input synthesis, application resources, or file changes.
 * At 160x200 only, pan oversized known application dialogs when focus changes.
 * Child geometry and font sizes remain intact. This is navigation, not reflow.
 */
#define WINVER 0x0300
#include <windows.h>
#include <string.h>
static HWND priorDialog,priorFocus;
static HFILE logFile=-1;
static void record(char *key,int n) {
    char b[80];int len;
    if(logFile==-1) return;
    len=wsprintf(b,"%s=%d\r\n",(LPSTR)key,n);_lwrite(logFile,b,len);
}
static BOOL allowed(HWND dialog) {
    HWND owner;char cls[40],title[80];
    GetClassName(dialog,cls,sizeof(cls));
    if(lstrcmp(cls,"#32770")) return FALSE;
    GetWindowText(dialog,title,sizeof(title));
    if(lstrcmpi(title,"About") && lstrcmpi(title,"About Notepad") &&
       lstrcmpi(title,"About Calculator") && lstrcmpi(title,"About Paintbrush") &&
       lstrcmpi(title,"File Open") &&
       lstrcmpi(title,"File Save") && lstrcmpi(title,"File Save As") &&
       lstrcmpi(title,"Save As") && lstrcmpi(title,"Notepad")) return FALSE;
    owner=GetWindow(dialog,GW_OWNER);
    if(!owner) return FALSE;
    GetClassName(owner,cls,sizeof(cls));
    return !lstrcmpi(cls,"Progman") || !lstrcmpi(cls,"Notepad") ||
           !lstrcmpi(cls,"SciCalc") || !lstrcmpi(cls,"Calc") ||
           !lstrcmpi(cls,"PBrush") || !lstrcmpi(cls,"pbParent");
}
static void reveal(void) {
    HWND dialog,focus;RECT r,c;int x,y,dx=0,dy=0,w,h;
    if(GetSystemMetrics(SM_CXSCREEN)!=160 || GetSystemMetrics(SM_CYSCREEN)!=200)
        return;
    dialog=GetActiveWindow();focus=GetFocus();
    if(!dialog || !focus || !IsWindowVisible(dialog) || !allowed(dialog) ||
       !IsChild(dialog,focus)) {priorDialog=priorFocus=NULL;return;}
    if(dialog==priorDialog && focus==priorFocus) return;
    priorDialog=dialog;priorFocus=focus;
    GetWindowRect(dialog,&r);w=r.right-r.left;h=r.bottom-r.top;
    if(w<=160 && h<=200) return;
    GetWindowRect(focus,&c);
    /* Never resize a child or force an oversized control into a smaller box. */
    if(c.right-c.left>156 || c.bottom-c.top>196) return;
    if(c.left<2) dx=2-c.left;
    else if(c.right>158) dx=158-c.right;
    if(c.top<2) dy=2-c.top;
    else if(c.bottom>198) dy=198-c.bottom;
    x=r.left+dx;y=r.top+dy;
    /* Bound panning to the existing dialog; retain its entire reachable range. */
    if(w>160) {if(x>0)x=0;if(x<160-w)x=160-w;}
    else {if(x<0)x=0;if(x>160-w)x=160-w;}
    if(h>200) {if(y>0)y=0;if(y<200-h)y=200-h;}
    else {if(y<0)y=0;if(y>200-h)y=200-h;}
    if(x!=r.left || y!=r.top) {
        record("OWNER_TASK",(int)GetWindowTask(dialog));
        record("FOCUS_ID",GetDlgCtrlID(focus));record("OLD_X",r.left);
        record("NEW_X",x);record("NEW_Y",y);
        SetWindowPos(dialog,NULL,x,y,0,0,SWP_NOSIZE|SWP_NOZORDER|SWP_NOACTIVATE);
    }
}
long FAR PASCAL ViewProc(HWND hwnd,UINT msg,WPARAM wp,LPARAM lp) {
    if(msg==WM_CREATE) {SetTimer(hwnd,1,250,NULL);return 0;}
    if(msg==WM_TIMER) {reveal();return 0;}
    if(msg==WM_CLOSE) {KillTimer(hwnd,1);DestroyWindow(hwnd);return 0;}
    if(msg==WM_DESTROY) {if(logFile!=-1)_lclose(logFile);PostQuitMessage(0);return 0;}
    return DefWindowProc(hwnd,msg,wp,lp);
}
int PASCAL WinMain(HINSTANCE instance,HINSTANCE previous,LPSTR args,int show) {
    WNDCLASS wc;MSG msg;HWND hwnd;char options[80];int n;
    for(n=0;n<79 && args[n];++n)options[n]=args[n];options[n]=0;
    hwnd=FindWindow("C16FocusView",NULL);
    if(strstr(options,"/OFF")) {if(hwnd)PostMessage(hwnd,WM_CLOSE,0,0L);return 0;}
    if(previous || hwnd) return 0;
    if(GetSystemMetrics(SM_CXSCREEN)!=160 || GetSystemMetrics(SM_CYSCREEN)!=200 ||
       !(LOWORD(GetWinFlags())&WF_CPU086)) return 1;
    if(strstr(options,"/LOG")) logFile=_lcreat("C:\\C16VIEW.TXT",0);
    memset(&wc,0,sizeof(wc));wc.lpfnWndProc=ViewProc;wc.hInstance=instance;
    wc.lpszClassName="C16FocusView";if(!RegisterClass(&wc))return 2;
    hwnd=CreateWindow("C16FocusView","Compact dialog focus reveal",WS_OVERLAPPED,
        0,0,0,0,NULL,NULL,instance,NULL);
    if(!hwnd)return 3;
    while(GetMessage(&msg,NULL,0,0)) {TranslateMessage(&msg);DispatchMessage(&msg);}
    return 0;
}
