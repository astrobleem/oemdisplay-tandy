/* Original Win3 software-screen capture harness. No VRAM/ports/hooks.
 * Captures actual screen DC through SRCCOPY/GetDIBits, not a mock desktop.
 * Private disposable fixture only; exits Windows after the sequence.
 */
#define WINVER 0x0300
#include <windows.h>
#include <string.h>
static HWND mainwin, dialogwin,calcwin,paintwin,qawin;
static HINSTANCE inst;
static int phase=-1;
static HFILE loghandle;
static FARPROC enumproc;
static char text[160];
static void line(char *s) { _lwrite(loghandle,s,strlen(s)); _lwrite(loghandle,"\r\n",2); }
static void number(char *key,int n) { wsprintf(text,"%s=%d",(LPSTR)key,n); line(text); }
BOOL FAR PASCAL EnumProc(HWND h,LONG unused)
{
    RECT r;
    char title[70],className[40];
    if (!IsWindowVisible(h)) return TRUE;
    GetWindowText(h,title,sizeof(title)); GetClassName(h,className,sizeof(className));
    GetWindowRect(h,&r);
    wsprintf(text,"WINDOW %s %s %d,%d,%d,%d",(LPSTR)className,(LPSTR)title,r.left,r.top,r.right,r.bottom);line(text);
    if (strstr(title,"Program Manager")) mainwin=h;
    if(strstr(title,"Calculator"))calcwin=h;
    if(strstr(title,"Paintbrush"))paintwin=h;
    if (strcmp(className,"#32770")==0 && !dialogwin) dialogwin=h;
    return TRUE;
}
static void inventory(void)
{
    dialogwin=NULL;
    EnumWindows(enumproc,0L);
}
static void dismiss(HWND dialog,int cancel)
{
    HWND child;char label[70],className[30];RECT r;
    if(!dialog) return;
    child=GetWindow(dialog,GW_CHILD);
    while(child) {
        GetWindowText(child,label,sizeof(label));GetClassName(child,className,sizeof(className));GetWindowRect(child,&r);
        wsprintf(text,"CONTROL %d %s %s %d,%d,%d,%d",GetDlgCtrlID(child),(LPSTR)className,(LPSTR)label,r.left,r.top,r.right,r.bottom);line(text);
        if(lstrcmpi(className,"Button")==0 && strstr(label,cancel?"Cancel":"OK"))
            PostMessage(dialog,WM_COMMAND,GetDlgCtrlID(child),MAKELONG(child,BN_CLICKED));
        child=GetWindow(child,GW_HWNDNEXT);
    }
}
static WORD command(HMENU menu,char *find)
{
    int i,n; WORD result,id; HMENU child; char name[100];
    n=GetMenuItemCount(menu);
    for(i=0;i<n;++i) {
        child=GetSubMenu(menu,i);
        if(child) { result=command(child,find); if(result) return result; }
        else {
            GetMenuString(menu,i,name,sizeof(name),MF_BYPOSITION);
            if(strstr(name,find)) { id=GetMenuItemID(menu,i);return id; }
        }
    }
    return 0;
}
static int capture(int id)
{
    HDC screen,memory; HBITMAP bitmap,old;
    HGLOBAL infoBlock,bitsBlock; LPBITMAPINFO info; LPSTR bits;
    HFILE file; DWORD size,offset; WORD zero; int rows,w,h,stride;
    char filename[24];
    w=GetSystemMetrics(SM_CXSCREEN);h=GetSystemMetrics(SM_CYSCREEN);
    stride=(w*4+31)/32*4;
    infoBlock=GlobalAlloc(GMEM_MOVEABLE|GMEM_ZEROINIT,sizeof(BITMAPINFOHEADER)+16*sizeof(RGBQUAD));
    bitsBlock=GlobalAlloc(GMEM_MOVEABLE|GMEM_ZEROINIT,(DWORD)stride*h);
    if(!infoBlock || !bitsBlock) return 0;
    info=(LPBITMAPINFO)GlobalLock(infoBlock);bits=GlobalLock(bitsBlock);
    info->bmiHeader.biSize=sizeof(BITMAPINFOHEADER);
    info->bmiHeader.biWidth=w;info->bmiHeader.biHeight=h;
    info->bmiHeader.biPlanes=1;info->bmiHeader.biBitCount=4;
    info->bmiHeader.biSizeImage=(DWORD)stride*h;info->bmiHeader.biClrUsed=16;
    screen=GetDC(NULL);memory=CreateCompatibleDC(screen);
    bitmap=CreateCompatibleBitmap(screen,w,h);old=SelectObject(memory,bitmap);
    number("SRCCOPY",BitBlt(memory,0,0,w,h,screen,0,0,SRCCOPY));
    SelectObject(memory,old);
    rows=GetDIBits(screen,bitmap,0,h,bits,info,DIB_RGB_COLORS);
    number("DIB_ROWS",rows);
    if(rows==h) {
        wsprintf(filename,"C:\\C%02d.BMP",id);
        file=_lcreat(filename,0);offset=14+sizeof(BITMAPINFOHEADER)+16*sizeof(RGBQUAD);
        size=offset+(DWORD)stride*h;zero=0;
        _lwrite(file,"BM",2);_lwrite(file,(LPSTR)&size,4);
        _lwrite(file,(LPSTR)&zero,2);_lwrite(file,(LPSTR)&zero,2);_lwrite(file,(LPSTR)&offset,4);
        _lwrite(file,(LPSTR)info,(WORD)(offset-14));_lwrite(file,bits,stride*h);_lclose(file);
    }
    DeleteObject(bitmap);DeleteDC(memory);ReleaseDC(NULL,screen);
    GlobalUnlock(bitsBlock);GlobalUnlock(infoBlock);GlobalFree(bitsBlock);GlobalFree(infoBlock);
    return rows==h;
}

static HWND editwin(HWND parent) {
    HWND h;char cls[40];h=GetWindow(parent,GW_CHILD);
    while(h) {GetClassName(h,cls,sizeof(cls));if(!lstrcmpi(cls,"Edit"))return h;h=GetWindow(h,GW_HWNDNEXT);}return NULL;
}
static void focusid(HWND d,int id) {
    HWND c;if(!d)return;c=GetDlgItem(d,id);if(!c)return;
    SetActiveWindow(d);SendMessage(d,WM_NEXTDLGCTL,(WPARAM)c,1L);
    number("FOCUS_ID",GetDlgCtrlID(GetFocus()));
}
static void push(HWND h) {
    if(!h)return;SetFocus(h);SendMessage(h,WM_KEYDOWN,VK_SPACE,1L);
    SendMessage(h,WM_KEYUP,VK_SPACE,0xc0000001L);
}
static void keybutton(HWND p,char *label) {
    HWND h;char name[50],cls[30];h=GetWindow(p,GW_CHILD);
    while(h) {GetWindowText(h,name,sizeof(name));GetClassName(h,cls,sizeof(cls));
      if(!lstrcmpi(cls,"Button") && !lstrcmp(name,label)) {push(h);return;}
      h=GetWindow(h,GW_HWNDNEXT);}
}
static void hits(HWND w) {
    RECT r;int x,y;if(!w)return;GetWindowRect(w,&r);
    x=r.left+GetSystemMetrics(SM_CXFRAME)+2;y=r.top+GetSystemMetrics(SM_CYFRAME)+3;
    number("HIT_SYSTEM",(int)SendMessage(w,WM_NCHITTEST,0,MAKELONG(x,y)));
    x=r.right-GetSystemMetrics(SM_CXFRAME)-3;
    number("HIT_MAX",(int)SendMessage(w,WM_NCHITTEST,0,MAKELONG(x,y)));
    x-=GetSystemMetrics(SM_CXSIZE);
    number("HIT_MIN",(int)SendMessage(w,WM_NCHITTEST,0,MAKELONG(x,y)));
    x=(r.left+r.right)/2;
    number("HIT_CAPTION",(int)SendMessage(w,WM_NCHITTEST,0,MAKELONG(x,y)));
    number("HIT_RIGHT",(int)SendMessage(w,WM_NCHITTEST,0,MAKELONG(r.right-1,(r.top+r.bottom)/2)));
}
long FAR PASCAL QAProc(HWND hwnd,UINT msg,WPARAM wp,LPARAM lp) {
    HDC dc;PAINTSTRUCT ps;int p;
    if(msg==WM_COMMAND) {number("QA_COMMAND",wp);return 0;}
    if(msg==WM_HSCROLL || msg==WM_VSCROLL) {
        p=GetScrollPos((HWND)HIWORD(lp),SB_CTL);
        if(wp==SB_LINEUP)--p;else if(wp==SB_LINEDOWN)++p;
        else if(wp==SB_THUMBPOSITION || wp==SB_THUMBTRACK)p=LOWORD(lp);
        SetScrollPos((HWND)HIWORD(lp),SB_CTL,p,TRUE);number("QA_SCROLL",p);return 0;
    }
    if(msg==WM_PAINT) {dc=BeginPaint(hwnd,&ps);TextOut(dc,4,111,"Native 32x16 icon",17);
        DrawIcon(dc,4,122,LoadIcon(NULL,IDI_APPLICATION));EndPaint(hwnd,&ps);return 0;}
    return DefWindowProc(hwnd,msg,wp,lp);
}
static HWND control(HWND parent,char *cls,char *title,DWORD style,int x,int y,int w,int h,int id) {
    return CreateWindow(cls,title,WS_CHILD|WS_VISIBLE|style,x,y,w,h,parent,(HMENU)id,inst,NULL);
}
static void makeqa(void) {
    WNDCLASS wc;HWND h;
    memset(&wc,0,sizeof(wc));wc.lpfnWndProc=QAProc;wc.hInstance=inst;
    wc.hbrBackground=GetStockObject(WHITE_BRUSH);wc.lpszClassName="C16QA";
    wc.hCursor=LoadCursor(NULL,IDC_ARROW);RegisterClass(&wc);
    qawin=CreateWindow("C16QA","Native controls",WS_OVERLAPPEDWINDOW,0,20,158,173,NULL,NULL,inst,NULL);
    control(qawin,"BUTTON","&Check",BS_AUTOCHECKBOX|WS_TABSTOP|WS_GROUP,4,3,110,10,101);
    control(qawin,"BUTTON","Radio &one",BS_AUTORADIOBUTTON|WS_TABSTOP|WS_GROUP,4,15,110,10,102);
    control(qawin,"BUTTON","Radio &two",BS_AUTORADIOBUTTON,4,27,110,10,103);
    control(qawin,"BUTTON","&Three state",BS_AUTO3STATE|WS_TABSTOP|WS_GROUP,4,39,110,10,104);
    control(qawin,"BUTTON","&Default",BS_DEFPUSHBUTTON|WS_TABSTOP,4,53,54,15,105);
    control(qawin,"BUTTON","Cancel",BS_PUSHBUTTON|WS_TABSTOP,64,53,44,15,106);
    control(qawin,"BUTTON","Disabled",BS_PUSHBUTTON|WS_DISABLED,4,72,54,15,107);
    h=control(qawin,"SCROLLBAR","",SBS_HORZ|WS_TABSTOP,4,94,120,8,108);
    SetScrollRange(h,SB_CTL,0,100,FALSE);SetScrollPos(h,SB_CTL,20,TRUE);
    h=control(qawin,"SCROLLBAR","",SBS_VERT|WS_TABSTOP,134,3,6,92,109);
    SetScrollRange(h,SB_CTL,0,100,FALSE);SetScrollPos(h,SB_CTL,30,TRUE);
    SendMessage(GetDlgItem(qawin,102),BM_SETCHECK,1,0L);
    ShowWindow(qawin,SW_SHOW);UpdateWindow(qawin);SetFocus(GetDlgItem(qawin,105));hits(qawin);
}

long FAR PASCAL WindowProc(HWND hwnd,UINT msg,WPARAM wp,LPARAM lp) {
    int step;char result[60];HWND note;WORD id;
    if(msg==WM_CREATE) {SetTimer(hwnd,1,2200,NULL);return 0;}
    if(msg==WM_TIMER) {
        step=phase++;number("PHASE",step);inventory();note=FindWindow("Notepad",NULL);
        if(step==-1) {number("CALC_EXEC",WinExec("CALC.EXE",SW_SHOW));}
        else if(step==0) {GetWindowText(GetDlgItem(calcwin,414),result,sizeof(result));line("INITIAL_DISPLAY");line(result);capture(0);}
        else if(step==1) {line("NO_SECOND_RESIZE=1");}
        else if(step==2) {capture(1);if(calcwin){SendMessage(calcwin,WM_COMMAND,49,0L);SendMessage(calcwin,WM_COMMAND,50,0L);SendMessage(calcwin,WM_COMMAND,92,0L);SendMessage(calcwin,WM_COMMAND,51,0L);SendMessage(calcwin,WM_COMMAND,111,0L);}}
        else if(step==3) {capture(2);if(calcwin){GetWindowText(GetDlgItem(calcwin,414),result,sizeof(result));line(result);dismiss(calcwin,0);PostMessage(calcwin,WM_CLOSE,0,0L);}}
        else if(step==4) {number("NOTE_EXEC",WinExec("NOTEPAD.EXE",SW_SHOW));}
        else if(step==5) {capture(3);if(note){id=command(GetMenu(note),"Open");number("OPEN_ID",id);if(id)PostMessage(note,WM_COMMAND,id,0L);}}
        else if(step==6) {capture(4);focusid(dialogwin,2);}
        else if(step==7) {capture(5);dismiss(dialogwin,1);}
        else if(step==8) {capture(6);if(note)PostMessage(note,WM_CLOSE,0,0L);}
        else if(step==9) {KillTimer(hwnd,1);line("COMPLETE=1");_lclose(loghandle);ExitWindows(0L,0);DestroyWindow(hwnd);PostQuitMessage(0);}
        return 0;
    }
    return DefWindowProc(hwnd,msg,wp,lp);
}
int PASCAL WinMain(HINSTANCE instance,HINSTANCE previous,LPSTR args,int show) {
    WNDCLASS wc;MSG msg;HWND hwnd;inst=instance;
    loghandle=_lcreat("C:\\CAPTURE.LOG",0);number("WindowsFlags",(int)LOWORD(GetWinFlags()));
    memset(&wc,0,sizeof(wc));wc.lpfnWndProc=WindowProc;wc.hInstance=instance;
    wc.lpszClassName="C16Capture";if(!RegisterClass(&wc))return 1;
    enumproc=MakeProcInstance((FARPROC)EnumProc,instance);
    hwnd=CreateWindow("C16Capture","Scoped native QA",WS_OVERLAPPED,0,0,0,0,NULL,NULL,instance,NULL);
    if(!hwnd)return 2;
    while(GetMessage(&msg,NULL,0,0)) {TranslateMessage(&msg);DispatchMessage(&msg);}
    FreeProcInstance(enumproc);return 0;
}
