/* SWAT: original graphics and rules for Windows 3.0 / 8088.
   Known-mode fullscreen renderer; slower GDI fallback. No driver patches, sound calls, hooks or saved settings. */
#define WINVER 0x0300
#include <windows.h>
#include "GAME.H"
static HDC back,atlas;
static HBITMAP bits,oldbits,sprites,oldsprites;
static int ox,oy,testing,bench,qaFailures,paints,liveBench,liveFrames;
static DWORD liveStarted;
static DWORD paintMs,maxPaint,startupMs;
static char logpath[144];
static const unsigned shape[4][12]={
 {0x000,0x606,0x909,0x969,0x7FE,0x1F8,0x1F8,0x3FC,0x492,0x204,0x000,0x000},
 {0x000,0x060,0x666,0x3FC,0x1F8,0x9F9,0x7FE,0x1F8,0x294,0x402,0x000,0x000},
 {0x801,0x402,0x204,0x108,0x090,0x060,0x060,0x090,0x108,0x204,0x402,0x801},
 {0x000,0x318,0x7BC,0x7FC,0x7FC,0x3F8,0x1F0,0x0E0,0x040,0x000,0x000,0x000}};

/* Fullscreen fast path: accepted driver tuples only; every other display uses GDI. */
static int closing,fastMode,fastReady,screenW,kind,banks,stride,byteCell,hideMouse,quitTest;
static int cursorX=80,cursorY=100;
static HDC fastDC;
static HCURSOR oldCursor;
static unsigned char bios,mono[16000],packed[256][4];
static unsigned offsets[200];
static HGLOBAL savedScreen;
static unsigned char FAR *saved;
static unsigned char FAR *vram=(unsigned char FAR *)0xb8000000L;
static DWORD restoreMs;
static const unsigned char tinyfont[36][7]={
 {14,17,19,21,25,17,14},{4,12,4,4,4,4,14},{14,17,1,2,4,8,31},{30,1,1,14,1,1,30},{2,6,10,18,31,2,2},
 {31,16,16,30,1,1,30},{14,16,16,30,17,17,14},{31,1,2,4,8,8,8},{14,17,17,14,17,17,14},{14,17,17,15,1,1,14},
 {14,17,17,31,17,17,17},{30,17,17,30,17,17,30},{15,16,16,16,16,16,15},{30,17,17,17,17,17,30},{31,16,16,30,16,16,31},
 {31,16,16,30,16,16,16},{15,16,16,19,17,17,15},{17,17,17,31,17,17,17},{14,4,4,4,4,4,14},{7,2,2,2,2,18,12},
 {17,18,20,24,20,18,17},{16,16,16,16,16,16,31},{17,27,21,21,17,17,17},{17,25,21,19,17,17,17},{14,17,17,17,17,17,14},
 {30,17,17,30,16,16,16},{14,17,17,17,21,18,13},{30,17,17,30,20,18,17},{15,16,16,14,1,1,30},{31,4,4,4,4,4,4},
 {17,17,17,17,17,17,14},{17,17,17,17,17,10,4},{17,17,17,21,21,21,10},{17,17,10,4,10,17,17},{17,17,10,4,4,4,4},{31,1,2,4,8,16,31}};
static int detectFast(void){HDC d;HMODULE mod;char path[128],*base;int i,col;
 screenW=GetSystemMetrics(SM_CXSCREEN);if(GetSystemMetrics(SM_CYSCREEN)!=200||GetWinFlags()&WF_PMODE)return 0;
 d=GetDC(NULL);col=GetDeviceCaps(d,NUMCOLORS);ReleaseDC(NULL,d);mod=GetModuleHandle("DISPLAY");path[0]=0;if(mod)GetModuleFileName(mod,path,sizeof(path));base=path;for(i=0;path[i];i++)if(path[i]=='\\'||path[i]==':')base=path+i+1;
 bios=*((unsigned char FAR *)0x00400049L);if(*((unsigned char FAR *)0x00400062L))return 0;banks=2;
 if(screenW==160&&col==16&&bios==8&&!lstrcmpi(base,"TNDY160.DRV"))kind=0;
 else if(screenW==320&&col==16&&bios==9&&!lstrcmpi(base,"TANDY88.DRV")){kind=0;banks=4;}
 else if(screenW==320&&col==4&&bios==4&&!lstrcmpi(base,"TNDY3204.DRV"))kind=1;
 else if(screenW==640&&col==4&&bios==10&&!lstrcmpi(base,"TNDY6404.DRV")){kind=2;banks=4;}
 else if(screenW==640&&col==2&&bios==6&&!lstrcmpi(base,"TNDY6402.DRV"))kind=3;
 else return 0;return 1;
}
static int owns(HWND w){HWND t;RECT r;if(closing)return 0;if(GetActiveWindow()!=w)return 0;if(*((unsigned char FAR *)0x00400049L)!=bios||*((unsigned char FAR *)0x00400062L))return 0;
 for(t=GetWindow(w,GW_HWNDPREV);t;t=GetWindow(t,GW_HWNDPREV))if(IsWindowVisible(t)&&!IsIconic(t)){GetWindowRect(t,&r);if(r.right>0&&r.bottom>0&&r.left<screenW&&r.top<200)return 0;}return 1;}
static void dotpixel(int x,int y){if(x>=0&&x<screenW&&y>=0&&y<200)mono[y*stride+(x>>3)]|=(unsigned char)(128>>(x&7));}
static void rawshape(int n,int x,int y){int r,c;unsigned v;for(r=0;r<12;r++){v=shape[n][r];for(c=0;c<12;c++)if(v&(0x800U>>c))dotpixel(ox+x+c,oy+y+r);}}
static void rawtext(int x,int y,char *t){int a,r,c,v;while(*t){a=*t>='0'&&*t<='9'?*t-'0':*t>='A'&&*t<='Z'?*t-'A'+10:-1;
 if(a>=0)for(r=0;r<7;r++){v=tinyfont[a][r];for(c=0;c<5;c++)if(v&(16>>c))dotpixel(ox+x+c,oy+y+r);}else if(*t==':'){dotpixel(ox+x+2,oy+y+2);dotpixel(ox+x+2,oy+y+5);}x+=6;t++;}}
static void rawbox(int x,int y,int xx,int yy){int i;for(i=x;i<=xx;i++){dotpixel(ox+i,oy+y);dotpixel(ox+i,oy+yy);}for(i=y;i<=yy;i++){dotpixel(ox+x,oy+i);dotpixel(ox+xx,oy+i);}}
static void rawScene(RECT *r){char b[24];int i;if(r->top<oy+29){wsprintf(b,"S:%05u",score);rawtext(3,2,b);for(i=0;i<hearts;i++)rawshape(3,104+i*13,1);rawtext(3,16,"CLICK TO SWAT");}if(r->left<ox+4||r->right>ox+144||r->top<oy+31||r->bottom>oy+143)rawbox(2,29,145,144);
 for(i=0;i<NFLY;i++)if(flies[i].active&&(flies[i].ttl>12||phase))rawshape(phase,flies[i].x-6,flies[i].y-6);if(marklife)rawshape(2,markx-6,marky-6);
 if(!playing||paused){if(!playing&&!hearts){rawtext(42,72,"GAME OVER");rawtext(30,89,"NEW: RESTART");}else if(paused){rawtext(56,72,"PAUSED");rawtext(42,89,"P: RESUME");}else{rawtext(48,72,"FLY SWAT");rawtext(32,89,"CLICK: START");}}
 if(r->bottom>oy+148){rawbox(2,149,43,172);rawbox(46,149,102,172);rawbox(105,149,145,172);rawtext(13,157,"NEW");rawtext(59,157,paused?"PLAY":"PAUSE");rawtext(114,157,"EXIT");}
 /* Small original swatter: lattice head and a short handle. */
 for(i=-4;i<=4;i++){dotpixel(cursorX+i,cursorY-4);dotpixel(cursorX+i,cursorY+4);dotpixel(cursorX-4,cursorY+i);dotpixel(cursorX+4,cursorY+i);dotpixel(cursorX+i,cursorY);dotpixel(cursorX,cursorY+i);}for(i=5;i<10;i++)dotpixel(cursorX+i-4,cursorY+i);
}
static void flushRaw(RECT *r){int x,y,j,a=r->left>>3,b=(r->right+7)>>3;unsigned off;unsigned char *p;if(a<0)a=0;if(b>stride)b=stride;
 for(y=r->top;y<r->bottom;y++)if(y>=0&&y<200)for(x=a;x<b;x++){p=packed[mono[y*stride+x]];off=offsets[y]+x*byteCell;for(j=0;j<byteCell;j++)vram[off+j]=p[j];}}
static void rawPaint(HWND w,RECT *r){RECT rc;int x,y,a=r->left>>3,b=(r->right+7)>>3;DWORD t=GetTickCount();if(!fastReady||!owns(w))return;
 if(a<0)a=0;if(b>stride)b=stride;for(y=r->top;y<r->bottom;y++)if(y>=0&&y<200)for(x=a;x<b;x++)mono[y*stride+x]=0;rc=*r;rc.left=a*8;rc.right=b*8;rawScene(&rc);flushRaw(&rc);t=GetTickCount()-t;paintMs+=t;if(t>maxPaint)maxPaint=t;if(testing)paints++;
}
static unsigned rawMismatch(void){int x,y,j;unsigned off,bad=0;unsigned char *p;for(y=0;y<200;y++)for(x=0;x<stride;x++){p=packed[mono[y*stride+x]];off=offsets[y]+x*byteCell;for(j=0;j<byteCell;j++)if(vram[off+j]!=p[j])bad++;}return bad;}
static int disrupted(void){int x,y,j,seen=0;unsigned off;unsigned char *p;
 for(y=oy+2;y<oy+9;y++)for(x=ox>>3;x<(ox>>3)+7;x++)if(mono[y*stride+x]){p=packed[mono[y*stride+x]];off=offsets[y]+x*byteCell;for(j=0;j<byteCell;j++)if(vram[off+j]!=p[j])return 1;if(++seen==12)return 0;}return 0;}
static void initFast(HWND w){POINT pt;int i,j,k,per,v,b;stride=screenW>>3;byteCell=kind==0?4:kind==3?1:2;
 for(i=0;i<200;i++)offsets[i]=(i&(banks-1))*8192U+(i/banks)*(banks==4?160:80);
 for(i=0;i<256;i++){if(kind==2){packed[i][0]=packed[i][1]=(unsigned char)i;}else{per=kind==0?2:kind==1?4:8;for(j=0;j<8;j+=per){b=0;for(k=0;k<per;k++){v=(i&(128>>(j+k)))?((1<<(8/per))-1):0;b=(b<<(8/per))|v;}packed[i][j/per]=(unsigned char)b;}}}
 fastDC=GetDC(NULL);if(!fastDC)return;GetCursorPos(&pt);cursorX=pt.x;cursorY=pt.y;if(cursorX<0)cursorX=0;if(cursorX>=screenW)cursorX=screenW-1;if(cursorY<0)cursorY=0;if(cursorY>199)cursorY=199;oldCursor=SetCursor(NULL);ShowCursor(FALSE);hideMouse=1;fastReady=1;
}
static void restoreFast(HWND w){DWORD t=GetTickCount();fastReady=0;if(fastDC&&*((unsigned char FAR *)0x00400049L)==bios&&*((unsigned char FAR *)0x00400062L)==0)BitBlt(fastDC,0,0,1,1,fastDC,0,0,SRCCOPY);
 if(hideMouse){SetCursor(oldCursor);ShowCursor(TRUE);hideMouse=0;}if(fastDC)ReleaseDC(NULL,fastDC);fastDC=NULL;restoreMs=GetTickCount()-t;
}

static void logtext(char *s){HFILE f=_lopen(logpath,OF_WRITE);if(f==HFILE_ERROR)f=_lcreat(logpath,0);if(f!=HFILE_ERROR){_llseek(f,0L,2);_lwrite(f,s,lstrlen(s));_lclose(f);}}
static void check(int ok,char *name){char b[160];wsprintf(b,"%s %s\r\n",(LPSTR)(ok?"PASS":"FAIL"),(LPSTR)name);logtext(b);if(!ok)qaFailures++;}
static void freecache(void){if(back){if(bits){SelectObject(back,oldbits);DeleteObject(bits);}DeleteDC(back);}if(atlas){if(sprites){SelectObject(atlas,oldsprites);DeleteObject(sprites);}DeleteDC(atlas);}back=atlas=NULL;bits=sprites=oldbits=oldsprites=NULL;}
static void setup(HDC d){SelectObject(d,GetStockObject(SYSTEM_FIXED_FONT));SetBkColor(d,RGB(0,0,0));SetTextColor(d,RGB(255,255,255));SetBkMode(d,TRANSPARENT);SelectObject(d,GetStockObject(WHITE_PEN));SelectObject(d,GetStockObject(BLACK_BRUSH));}
static void pixelshape(HDC d,int n,int x,int y){int r,c,a;unsigned row;for(r=0;r<12;r++){row=shape[n][r];c=0;while(c<12){if(row&(0x800U>>c)){a=c;while(c<12&&(row&(0x800U>>c)))c++;PatBlt(d,x+a,y+r,c-a,1,WHITENESS);}else c++;}}}
static int cache(HDC d){int i;if(back&&atlas)return 1;freecache();back=CreateCompatibleDC(d);atlas=CreateCompatibleDC(d);if(!back||!atlas){freecache();return 0;}bits=CreateCompatibleBitmap(d,FW,FH);sprites=CreateCompatibleBitmap(d,48,12);if(!bits||!sprites){freecache();return 0;}oldbits=SelectObject(back,bits);oldsprites=SelectObject(atlas,sprites);if(!oldbits||!oldsprites){freecache();return 0;}PatBlt(back,0,0,FW,FH,BLACKNESS);PatBlt(atlas,0,0,48,12,BLACKNESS);for(i=0;i<4;i++)pixelshape(atlas,i,i*12,0);return 1;}
static void spr(HDC d,int n,int x,int y){if(atlas)BitBlt(d,x,y,12,12,atlas,n*12,0,SRCCOPY);else pixelshape(d,n,x,y);}
static void label(HDC d,int x,int y,char *s){TextOut(d,x,y,s,lstrlen(s));}
static void box(HDC d,int x,int y,int xx,int yy){MoveTo(d,x,y);LineTo(d,xx,y);LineTo(d,xx,yy);LineTo(d,x,yy);LineTo(d,x,y);}
static void scene(HDC d,RECT *r){char b[24];int i;setup(d);PatBlt(d,r->left,r->top,r->right-r->left,r->bottom-r->top,BLACKNESS);
 if(r->top<29){wsprintf(b,"S:%05u",score);label(d,3,2,b);for(i=0;i<hearts;i++)spr(d,3,104+i*13,1);label(d,3,16,"CLICK TO SWAT");}
 if(r->bottom>24&&r->top<149){if(r->left<4||r->right>144||r->top<31||r->bottom>143)box(d,2,29,145,144);for(i=0;i<NFLY;i++)if(flies[i].active&&(flies[i].ttl>12||phase))spr(d,phase,flies[i].x-6,flies[i].y-6);
 if(marklife)spr(d,2,markx-6,marky-6);
 if(!playing||paused){PatBlt(d,13,69,123,37,BLACKNESS);if(!playing&&hearts==0){label(d,22,72,"GAME OVER");label(d,13,89,"NEW: restart");}else if(paused){label(d,32,72,"PAUSED");label(d,13,89,"P: resume");}else{label(d,22,72,"FLY SWAT");label(d,13,89,"Click: start");}}
 }
 if(r->bottom>148){box(d,2,149,43,172);box(d,46,149,102,172);box(d,105,149,145,172);label(d,7,155,"NEW");label(d,49,155,paused?"PLAY":"PAUSE");label(d,109,155,"EXIT");}
}
static void paint(HWND w,HDC d,RECT *r){RECT a,c;DWORD start=GetTickCount(),dt;GetClientRect(w,&c);if(r->left<ox)PatBlt(d,0,0,ox,c.bottom,BLACKNESS);if(r->right>ox+FW)PatBlt(d,ox+FW,0,c.right-ox-FW,c.bottom,BLACKNESS);if(r->bottom>oy+FH)PatBlt(d,0,oy+FH,c.right,c.bottom-oy-FH,BLACKNESS);a=*r;OffsetRect(&a,-ox,-oy);if(a.left<0)a.left=0;if(a.top<0)a.top=0;if(a.right>FW)a.right=FW;if(a.bottom>FH)a.bottom=FH;
 if(a.left<a.right&&a.top<a.bottom){if(cache(d)){scene(back,&a);BitBlt(d,ox+a.left,oy+a.top,a.right-a.left,a.bottom-a.top,back,a.left,a.top,SRCCOPY);}else{SetViewportOrg(d,ox,oy);scene(d,&a);SetViewportOrg(d,0,0);}}
 dt=GetTickCount()-start;paintMs+=dt;if(dt>maxPaint)maxPaint=dt;if(testing)paints++;
}
static void dirty(HWND w,int x,int y,int xx,int yy){RECT r;r.left=ox+x;r.top=oy+y;r.right=ox+xx;r.bottom=oy+yy;InvalidateRect(w,&r,FALSE);}
static void dirtyflies(HWND w){int i;for(i=0;i<NFLY;i++)if(flies[i].active)dirty(w,flies[i].x-8,flies[i].y-8,flies[i].x+9,flies[i].y+9);if(marklife)dirty(w,markx-7,marky-7,markx+8,marky+8);}
static void pausegame(HWND w){if(playing){paused=!paused;InvalidateRect(w,NULL,FALSE);}}
static void capture(char *name){HFILE f;char path[144];unsigned char FAR *vram=(unsigned char FAR *)0xb8000000L;int i;unsigned char mode=*((unsigned char FAR *)0x00400049L);if(mode!=4&&mode!=6&&mode!=8&&mode!=9&&mode!=10)return;lstrcpy(path,logpath);for(i=lstrlen(path)-1;i>=0&&path[i]!='\\';i--);path[i+1]=0;lstrcat(path,name);f=_lcreat(path,0);if(f!=HFILE_ERROR){_lwrite(f,(LPSTR)vram,(mode==9||mode==10)?32768U:16384U);_lclose(f);}}
static void queueClose(HWND w){if(!closing){closing=1;PostMessage(w,WM_CLOSE,0,0L);}}
LONG FAR PASCAL WndProc(HWND w,UINT m,WPARAM wp,LPARAM lp){HDC d;PAINTSTRUCT ps;RECT r;int x,y,oldh,k;unsigned olds;char liveLog[180];switch(m){
 case WM_CREATE:hearts=3;playing=paused=0;if(!SetTimer(w,1,220,NULL))return -1L;return 0;
 case WM_SIZE:GetClientRect(w,&r);ox=(r.right-FW)/2;oy=fastMode?12:0;InvalidateRect(w,NULL,FALSE);return 0;
 case WM_ERASEBKGND:return 1;
 case WM_PAINT:d=BeginPaint(w,&ps);if(fastMode)rawPaint(w,&ps.rcPaint);else paint(w,d,&ps.rcPaint);EndPaint(w,&ps);return 0;
 case WM_SETCURSOR:if(fastMode){SetCursor(NULL);return 1;}break;
 case WM_MOUSEMOVE:if(fastMode&&fastReady){dirty(w,cursorX-ox-6,cursorY-oy-6,cursorX-ox+8,cursorY-oy+11);cursorX=(int)LOWORD(lp);cursorY=(int)HIWORD(lp);dirty(w,cursorX-ox-6,cursorY-oy-6,cursorX-ox+8,cursorY-oy+11);}return 0;
 case WM_ACTIVATE:if(fastMode){if(fastReady&&wp==WA_INACTIVE)queueClose(w);return 0;}break;
 case WM_ACTIVATEAPP:if(fastMode){if(fastReady&&!wp)queueClose(w);return 0;}break;
 case WM_CANCELMODE:if(fastMode){if(fastReady)queueClose(w);return 0;}break;
 case WM_LBUTTONDOWN:x=(int)LOWORD(lp)-ox;y=(int)HIWORD(lp)-oy;
  if(y>=149&&y<=172){if(x>=105&&x<=145){DestroyWindow(w);return 0;}if(x>=2&&x<=43){newgame();InvalidateRect(w,NULL,FALSE);}else if(x>=46&&x<=102)pausegame(w);return 0;}
  if(x<3||x>=145||y<30||y>=144)return 0;if(!playing){if(hearts){newgame();InvalidateRect(w,NULL,FALSE);}return 0;}if(paused)return 0;dirtyflies(w);oldh=hearts;olds=score;swat(x,y);dirtyflies(w);if(oldh!=hearts||olds!=score)dirty(w,0,0,FW,15);if(!playing)InvalidateRect(w,NULL,FALSE);return 0;
 case WM_KEYDOWN:if(lp&0x40000000L)return 0;if(wp=='N'||wp=='R'){newgame();InvalidateRect(w,NULL,FALSE);}else if(wp=='P'||wp==VK_SPACE){if(!playing){newgame();InvalidateRect(w,NULL,FALSE);}else pausegame(w);}else if(wp==VK_ESCAPE)DestroyWindow(w);return 0;
 case WM_KILLFOCUS:if(fastMode&&fastReady){queueClose(w);return 0;}if(playing&&!paused){paused=1;InvalidateRect(w,NULL,FALSE);}return 0;
 case WM_TIMER:if(fastMode&&fastReady&&!owns(w)){queueClose(w);return 0;}if(fastMode&&fastReady&&disrupted())InvalidateRect(w,NULL,FALSE);if(wp!=1||!playing||paused||IsIconic(w))return 0;if(liveBench)for(k=0;k<NFLY;k++)if(flies[k].active)flies[k].ttl=90;oldh=hearts;dirtyflies(w);stepgame();dirtyflies(w);if(oldh!=hearts)dirty(w,0,0,FW,15);if(!playing)InvalidateRect(w,NULL,FALSE);if(liveBench){UpdateWindow(w);if(!liveFrames)liveStarted=GetTickCount();if(++liveFrames==40){wsprintf(liveLog,"LIVE timers=40 measured_intervals=39 elapsed_ms=%lu paints=%d paint_ms=%lu max_paint_ms=%lu\r\n",GetTickCount()-liveStarted,paints,paintMs,maxPaint);logtext(liveLog);DestroyWindow(w);}}return 0;
 case WM_CLOSE:DestroyWindow(w);return 0;
 case WM_DESTROY:KillTimer(w,1);playing=0;if(fastMode)restoreFast(w);freecache();PostQuitMessage(0);return 0;
 }return DefWindowProc(w,m,wp,lp);}
static void runtests(HWND w){MSG closeMsg;HWND cover;int x,y,h,i,j;unsigned s,t;DWORD started;char b[220];RECT r;
 KillTimer(w,1);GetClientRect(w,&r);wsprintf(b,"START screen=%dx%d client=%dx%d cache=%d initial_draw_ms=%lu fast=%d\r\n",GetSystemMetrics(SM_CXSCREEN),GetSystemMetrics(SM_CYSCREEN),r.right,r.bottom,back!=NULL&&atlas!=NULL,startupMs,fastMode);logtext(b);check(fastMode?fastReady:(back!=NULL&&atlas!=NULL),"renderer allocation");if(quitTest){if(quitTest>=4){logtext("QA cover create\r\n");cover=CreateWindow("STATIC","",WS_POPUP|SS_WHITERECT,0,0,screenW,200,NULL,NULL,GetWindowWord(w,GWW_HINSTANCE),NULL);logtext("QA cover position\r\n");SetWindowPos(cover,HWND_TOP,0,0,screenW,200,SWP_NOACTIVATE|SWP_SHOWWINDOW);logtext("QA cover paint\r\n");UpdateWindow(cover);logtext("QA cover activate\r\n");if(quitTest==4)SetActiveWindow(cover);else SendMessage(w,WM_TIMER,1,0L);check(closing,"focus or occlusion requests close");if(IsWindow(w)&&PeekMessage(&closeMsg,w,WM_CLOSE,WM_CLOSE,PM_REMOVE))DispatchMessage(&closeMsg);check(!IsWindow(w),"real focus or full occlusion exits");DestroyWindow(cover);UpdateWindow(GetDesktopWindow());}else SendMessage(w,quitTest==1?WM_KILLFOCUS:quitTest==2?WM_KEYDOWN:WM_CLOSE,quitTest==2?VK_ESCAPE:0,0L);if(IsWindow(w)&&PeekMessage(&closeMsg,w,WM_CLOSE,WM_CLOSE,PM_REMOVE))DispatchMessage(&closeMsg);check(!fastReady&&!fastDC,"alternate exit cleanup");return;}
 SendMessage(w,WM_LBUTTONDOWN,0,MAKELONG(ox+70,oy+90));check(playing&&hearts==3,"mouse starts game");
 x=flies[0].x;y=flies[0].y;SendMessage(w,WM_LBUTTONDOWN,0,MAKELONG(ox+x,oy+y));check(score==10&&hearts==3,"mouse hit scores");
 SendMessage(w,WM_LBUTTONDOWN,0,MAKELONG(ox+6,oy+34));check(hearts==2&&score==10,"mouse miss loses life");
 SendMessage(w,WM_KEYDOWN,'P',0L);x=flies[0].x;y=flies[0].y;t=ticks;SendMessage(w,WM_TIMER,1,0L);SendMessage(w,WM_LBUTTONDOWN,0,MAKELONG(ox+x,oy+y));check(paused&&ticks==t&&flies[0].x==x&&score==10,"pause blocks timer and clicks");
 SendMessage(w,WM_LBUTTONDOWN,0,MAKELONG(ox+75,oy+160));check(!paused,"mouse resumes");if(!fastMode){SendMessage(w,WM_KILLFOCUS,0,0L);check(paused,"focus loss pauses");}
 SendMessage(w,WM_LBUTTONDOWN,0,MAKELONG(ox+20,oy+160));check(playing&&!paused&&hearts==3&&score==0,"mouse new game");
 for(i=0;i<3;i++)SendMessage(w,WM_LBUTTONDOWN,0,MAKELONG(ox+6,oy+34));check(!playing&&!hearts,"three misses game over");SendMessage(w,WM_KEYDOWN,'N',0L);check(playing&&hearts==3&&!score,"keyboard restart");
 for(i=0;i<NFLY;i++){flies[i].ttl=1;flies[i].active=1;}SendMessage(w,WM_TIMER,1,0L);check(!playing&&!hearts,"three escapes game over");
 newgame();for(i=0;i<NFLY;i++){flies[i].x=20+i*50;flies[i].y=60+i*25;}score=120;UpdateWindow(w);InvalidateRect(w,NULL,FALSE);UpdateWindow(w);capture("SWAT.RAW");
 if(fastMode&&!bench){SendMessage(w,WM_MOUSEMOVE,0,MAKELONG(0,0));UpdateWindow(w);check(rawMismatch()==0,"swatter top-left clipping");SendMessage(w,WM_MOUSEMOVE,0,MAKELONG(screenW-1,199));UpdateWindow(w);check(rawMismatch()==0,"swatter bottom-right clipping");SendMessage(w,WM_MOUSEMOVE,0,MAKELONG(ox+flies[0].x,oy+flies[0].y));UpdateWindow(w);check(rawMismatch()==0,"swatter fly overlap");}
 if(fastMode){BitBlt(fastDC,0,0,1,1,fastDC,0,0,SRCCOPY);check(disrupted(),"shadow overwrite detected");SendMessage(w,WM_TIMER,1,0L);UpdateWindow(w);check(!disrupted(),"shadow overwrite repaired");}
 paintMs=maxPaint=0;paints=0;started=GetTickCount();for(i=0;i<(bench?12:60);i++){for(j=0;j<NFLY;j++)if(flies[j].active)flies[j].ttl=90;SendMessage(w,WM_TIMER,1,0L);if(!bench&&i%9==0){j=0;if(flies[j].active)SendMessage(w,WM_LBUTTONDOWN,0,MAKELONG(ox+flies[j].x,oy+flies[j].y));}UpdateWindow(w);}
 wsprintf(b,"BENCH frames=%d elapsed_ms=%lu paint_ms=%lu max_paint_ms=%lu score=%u free=%lu\r\n",paints,GetTickCount()-started,paintMs,maxPaint,score,GetFreeSpace(0));logtext(b);check(playing&&hearts==3&&score>=(bench?120U:130U),"animated native frames");
 h=hearts;s=score;SendMessage(w,WM_KEYDOWN,'P',0L);UpdateWindow(w);for(i=0;i<5;i++)SendMessage(w,WM_TIMER,1,0L);check(paused&&hearts==h&&score==s,"repeated paused ticks");
 SendMessage(w,WM_LBUTTONDOWN,0,MAKELONG(ox+125,oy+160));check(!back&&!atlas&&!fastDC&&!fastReady,"exit frees resources");wsprintf(b,"QA failures=%d\r\n",qaFailures);logtext(b);
}
int PASCAL WinMain(HINSTANCE inst,HINSTANCE prev,LPSTR cmd,int show){WNDCLASS wc;HWND w;MSG msg;int i,j;HFILE f;DWORD start;unsigned bad=0;
 testing=cmd[0]=='/'&&(cmd[1]=='T'||cmd[1]=='t'||cmd[1]=='B'||cmd[1]=='b');bench=cmd[0]=='/'&&(cmd[1]=='B'||cmd[1]=='b');quitTest=cmd[0]=='/'&&(cmd[1]=='Q'||cmd[1]=='q')?1:cmd[0]=='/'&&(cmd[1]=='E'||cmd[1]=='e')?2:cmd[0]=='/'&&(cmd[1]=='W'||cmd[1]=='w')?3:cmd[0]=='/'&&(cmd[1]=='A'||cmd[1]=='a')?4:cmd[0]=='/'&&(cmd[1]=='O'||cmd[1]=='o')?5:0;if(quitTest)testing=1;liveBench=cmd[0]=='/'&&(cmd[1]=='R'||cmd[1]=='r');if(liveBench)testing=1;fastMode=detectFast();if(cmd[0]=='/'&&(cmd[1]=='F'||cmd[1]=='f')){testing=1;fastMode=0;}if(cmd[0]=='/'&&(cmd[1]=='G'||cmd[1]=='g'))fastMode=0;GetModuleFileName(inst,logpath,sizeof(logpath));for(i=lstrlen(logpath)-1;i>=0&&logpath[i]!='\\';i--);logpath[i+1]=0;lstrcat(logpath,"SWAT.LOG");if(testing){f=_lcreat(logpath,0);if(f!=HFILE_ERROR)_lclose(f);}
 if(GetSystemMetrics(SM_CXSCREEN)<160||GetSystemMetrics(SM_CYSCREEN)<200)return 1;
 if(!prev){wc.style=0;wc.lpfnWndProc=WndProc;wc.cbClsExtra=wc.cbWndExtra=0;wc.hInstance=inst;wc.hIcon=NULL;wc.hCursor=LoadCursor(NULL,IDC_CROSS);wc.hbrBackground=GetStockObject(BLACK_BRUSH);wc.lpszMenuName=NULL;wc.lpszClassName="TandyFlySwat";if(!RegisterClass(&wc))return 2;}
 if(testing&&fastMode){capture("BEFORE.RAW");savedScreen=GlobalAlloc(GMEM_MOVEABLE,32768UL);if(savedScreen)saved=(unsigned char FAR *)GlobalLock(savedScreen);if(saved)for(j=0;j<(banks==4?4:2);j++)for(i=0;i<8192;i++)saved[j*8192U+i]=vram[j*8192U+i];}
 w=CreateWindow("TandyFlySwat","Fly Swat",fastMode?WS_POPUP:WS_OVERLAPPED|WS_CAPTION|WS_SYSMENU,fastMode?0:(GetSystemMetrics(SM_CXSCREEN)-156)/2,0,fastMode?screenW:156,fastMode?200:198,NULL,NULL,inst,NULL);if(!w)return 3;start=GetTickCount();if(fastMode)initFast(w);if(fastMode&&!fastReady){DestroyWindow(w);if(saved){GlobalUnlock(savedScreen);GlobalFree(savedScreen);}return 4;}ShowWindow(w,show);UpdateWindow(w);startupMs=GetTickCount()-start;if(liveBench){char b[120];newgame();InvalidateRect(w,NULL,FALSE);UpdateWindow(w);paintMs=maxPaint=0;paints=0;wsprintf(b,"LIVE START initial_draw_ms=%lu fast=%d width=%d\r\n",startupMs,fastMode,screenW);logtext(b);}else if(testing)runtests(w);while(GetMessage(&msg,NULL,0,0)){TranslateMessage(&msg);DispatchMessage(&msg);if(closing&&IsWindow(w))DestroyWindow(w);}if(testing&&fastMode){HDC d;unsigned initialBad=0;capture("AFTER.RAW");if(saved){for(i=0;i<200;i++)for(j=0;j<(banks==4?160:80);j++){if(saved[offsets[i]+j]!=vram[offsets[i]+j])initialBad++;saved[offsets[i]+j]=vram[offsets[i]+j];}d=GetDC(NULL);if(d){if(!BitBlt(d,0,0,1,1,d,0,0,SRCCOPY))bad=65535U;ReleaseDC(NULL,d);}else bad=65535U;if(!bad)for(i=0;i<200;i++)for(j=0;j<(banks==4?160:80);j++)if(saved[offsets[i]+j]!=vram[offsets[i]+j])bad++;GlobalUnlock(savedScreen);GlobalFree(savedScreen);saved=NULL;}else bad=65535U;{char b[140];wsprintf(b,"RESTORE initial_changed_bytes=%u canonical_changed_bytes=%u restore_ms=%lu\r\n",initialBad,bad,restoreMs);logtext(b);}check(bad==0,"current Windows shadow restored");if(!liveBench)check(initialBad==0,"controlled baseline restored");}if(testing)logtext("QUIT clean\r\n");return qaFailures?4:0;
}
