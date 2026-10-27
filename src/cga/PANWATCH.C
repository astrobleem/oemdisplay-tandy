#include <windows.h>
/* Private CGAPAN observer: developer instrumentation, never a consumer file.
 * A hidden window polls four times a second and logs C:\PANWATCH.LOG: the
 * viewport origin, the active and focused windows with their logical rects,
 * whether each lies inside the viewport, the active window's child controls
 * with a hit test of each center, and the free global heap. It sends no input
 * and takes no focus, so real applications run undisturbed. */
#define ESC_XY 0x5860
#define VIEW_W 160
#define VIEW_H 100
#define MAX_TREE 48
static HWND win,last_focus,last_active;
static int view_x,view_y,have_view,settle,last_owners=-1,edge,ticks;
static POINT last_cur;
static int dlg_seen,dlg_fired,dlg_wait;
static DWORD last_free;
static char line[256],cls[40],txt[40];
static void Log(LPSTR s)
{
    OFSTRUCT of;
    int f=OpenFile("C:\\PANWATCH.LOG",&of,OF_WRITE);
    if(f==-1)f=OpenFile("C:\\PANWATCH.LOG",&of,OF_CREATE|OF_WRITE);
    if(f==-1)return;
    _llseek(f,0L,2);_lwrite(f,s,lstrlen(s));_lclose(f);
}
static int Query(int FAR *out)
{
    HDC dc=GetDC(win);
    int in[2],r;
    in[0]=-1;in[1]=0;
    r=Escape(dc,ESC_XY,4,(LPSTR)in,(LPSTR)out);
    ReleaseDC(win,dc);
    return r;
}
static int Inside(RECT *r)
{
    return r->left>=view_x&&r->top>=view_y&&
        r->right<=view_x+VIEW_W&&r->bottom<=view_y+VIEW_H;
}
static void Describe(LPSTR tag,HWND w)
{
    RECT r;
    cls[0]=txt[0]=0;
    GetClassName(w,cls,sizeof(cls));GetWindowText(w,txt,sizeof(txt));
    GetWindowRect(w,&r);
    wsprintf(line,"%s h=%04x cls=%s txt=%s rect=%d,%d,%d,%d view=%d,%d in=%d\r\n",
        tag,(int)w,(LPSTR)cls,(LPSTR)txt,r.left,r.top,r.right,r.bottom,
        view_x,view_y,Inside(&r));
    Log(line);
}
static void Tree(HWND parent)
{
    HWND c;RECT r;POINT p;int n=0;
    for(c=GetWindow(parent,GW_CHILD);c&&n<MAX_TREE;c=GetWindow(c,GW_HWNDNEXT),n++){
        cls[0]=txt[0]=0;
        GetClassName(c,cls,sizeof(cls));GetWindowText(c,txt,sizeof(txt));
        GetWindowRect(c,&r);
        p.x=(r.left+r.right)/2;p.y=(r.top+r.bottom)/2;
        wsprintf(line," C h=%04x cls=%s txt=%s rect=%d,%d,%d,%d style=%04x en=%d vis=%d hit=%04x\r\n",
            (int)c,(LPSTR)cls,(LPSTR)txt,r.left,r.top,r.right,r.bottom,
            (int)(GetWindowLong(c,GWL_STYLE)>>16),IsWindowEnabled(c),
            IsWindowVisible(c),(int)WindowFromPoint(p));
        Log(line);
    }
    Log(" TREE END\r\n");
}
static void Tick(void)
{
    int out[6],now_x,now_y,owners;HWND f,a;DWORD fr;POINT cur;
    owners=((int)FindWindow("CGAPan",NULL)!=0)|
        (((int)FindWindow("CGASlide",NULL)!=0)<<1);
    if(owners!=last_owners){
        last_owners=owners;
        wsprintf(line,"OWNER pan=%d slide=%d\r\n",owners&1,owners>>1);
        Log(line);
    }
    if(Query(out)>0){
        now_x=out[0];now_y=out[1];
        if(!have_view||now_x!=view_x||now_y!=view_y){
            have_view=1;view_x=now_x;view_y=now_y;
            wsprintf(line,"VIEW %d,%d t=%lu\r\n",view_x,view_y,GetTickCount());
            Log(line);
            last_focus=NULL;
        }
    }
    a=GetActiveWindow();
    if(a&&a!=last_active){last_active=a;settle=6;Describe("ACTIVE",a);}
    f=GetFocus();
    if(f&&f!=last_focus){last_focus=f;Describe("FOCUS",f);}
    if(settle&&--settle==0&&last_active&&IsWindow(last_active)){
        Describe("SETTLED",last_active);Tree(last_active);
    }
    GetCursorPos(&cur);
    if(cur.x!=last_cur.x||cur.y!=last_cur.y){
        last_cur=cur;
        wsprintf(line,"CURSOR %d,%d view=%d,%d\r\n",cur.x,cur.y,view_x,view_y);
        Log(line);
    }
    ticks++;
    if(edge==2){
        /* After the settings window has come and gone, push the pointer to
         * the right edge once; whether the view scrolls shows the setting. */
        if(FindWindow("PanSetDlg",NULL))dlg_seen=1;
        else if(dlg_seen&&!dlg_fired&&++dlg_wait>=32){
            dlg_fired=1;SetCursorPos(view_x+VIEW_W-2,view_y+50);
            wsprintf(line,"EDGE after settings view=%d,%d\r\n",view_x,view_y);
            Log(line);
        }
    }
    if(edge==1&&have_view&&ticks%160==0&&ticks<=640){
        /* One edge per 40 s, one pixel in: right, bottom, left, top. Each
         * scrolls away from the previous corner so the move is possible. */
        switch(ticks/160){
        case 1:SetCursorPos(view_x+VIEW_W-2,view_y+50);break;
        case 2:SetCursorPos(view_x+80,view_y+VIEW_H-2);break;
        case 3:SetCursorPos(view_x+1,view_y+50);break;
        case 4:SetCursorPos(view_x+80,view_y+1);break;
        }
        wsprintf(line,"EDGE test %d view=%d,%d\r\n",ticks/160,view_x,view_y);
        Log(line);
    }
    fr=GetFreeSpace(0);
    if(fr!=last_free){
        last_free=fr;wsprintf(line,"FREE %08lx\r\n",fr);Log(line);
    }
}
/* Async key states of the chord keys, logged only when they change. */
static void KeyLog(void)
{
    static int vk[14]={VK_CONTROL,VK_MENU,VK_HOME,VK_END,VK_LEFT,VK_RIGHT,
        VK_UP,VK_DOWN,VK_NUMPAD7,VK_NUMPAD1,VK_NUMPAD4,VK_NUMPAD6,
        VK_NUMPAD8,VK_NUMPAD2};
    static unsigned last;
    unsigned mask=0;
    int i;
    for(i=0;i<14;i++)if(GetAsyncKeyState(vk[i])&0x8000)mask|=1u<<i;
    if(mask!=last){
        last=mask;
        wsprintf(line,"KEYS %04x ctl=%d alt=%d home=%d end=%d left=%d right=%d up=%d down=%d pad=%d%d%d%d%d%d t=%lu\r\n",
            mask,mask&1,(mask>>1)&1,(mask>>2)&1,(mask>>3)&1,(mask>>4)&1,
            (mask>>5)&1,(mask>>6)&1,(mask>>7)&1,(mask>>8)&1,(mask>>9)&1,
            (mask>>10)&1,(mask>>11)&1,(mask>>12)&1,(mask>>13)&1,
            GetTickCount());
        Log(line);
    }
}
long FAR PASCAL WndProc(HWND w,WORD m,WORD wp,LONG lp)
{
    switch(m){
    case WM_TIMER:if(wp==2)KeyLog();else Tick();return 0L;
    case WM_DESTROY:PostQuitMessage(0);return 0L;
    }
    return DefWindowProc(w,m,wp,lp);
}
int PASCAL WinMain(HANDLE inst,HANDLE prev,LPSTR cmd,int show)
{
    WNDCLASS wc;MSG msg;
    if(!prev){
        wc.style=0;wc.lpfnWndProc=WndProc;wc.cbClsExtra=wc.cbWndExtra=0;
        wc.hInstance=inst;wc.hIcon=NULL;wc.hCursor=NULL;
        wc.hbrBackground=NULL;wc.lpszMenuName=NULL;wc.lpszClassName="PanWatch";
        if(!RegisterClass(&wc))return 1;
    }
    win=CreateWindow("PanWatch","PANWATCH",WS_POPUP,0,0,1,1,NULL,NULL,inst,NULL);
    if(!win)return 1;
    edge=GetProfileInt("PanWatch","Edge",0);
    SetTimer(win,1,250,NULL);SetTimer(win,2,55,NULL);
    wsprintf(line,"PANWATCH START screen=%dx%d\r\n",
        GetSystemMetrics(SM_CXSCREEN),GetSystemMetrics(SM_CYSCREEN));
    Log(line);
    while(GetMessage(&msg,NULL,0,0)){TranslateMessage(&msg);DispatchMessage(&msg);}
    return msg.wParam;
}
