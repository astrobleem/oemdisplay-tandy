/* Rotating cube. Windows 3.0 real mode / 8088. GDI owns every displayed pixel.
   Input drain policy adapted from this project's first-party Starfield saver. */
#define WINVER 0x0300
#include <windows.h>
#include "CUBECORE.H"
#define ID_STYLE 101
#define ID_SPEED 102
#define ID_SIZE 103
#define ID_PREVIEW 104
#define ID_SAVE 105
#define ID_CLOSE 106
static HINSTANCE instance;
static HWND saver, config, previousActive, previousFocus, qa;
static HDC canvas;
static HBITMAP bitmap, oldBitmap;
static HBRUSH shades[17], solids[17];
static HPEN edge;
static HCURSOR blankCursor, previousCursor;
static BYTE cursorAnd[128], cursorXor[128], initialKeys[256], downKeys[256];
static int style, speed=2, cubeSize=2, selectedStyle, selectedSpeed, selectedSize;
static int screenW, screenH, viewX, viewY, viewW, viewH, colors, cw, ch, scaleX, scaleY, timerOn;
static int lastX, lastY;
static int running, draining, closing, returnFocus, hidden, mouseHeld, mouseGesture;
static int benchmark, qaMode, qaStep, qaFrames, qaLeaks, qaDone, errors, frames;
static int previewPending, shutdown, showConfig;
static unsigned phase;
static DWORD armedAt, lastInput, lastFrame, phaseTime, drawTotal, drawMax, start;
static POINT origin;
static char logpath[144], ini[144], wakeReason[32];
static CFRAME frame;
static char *styles[4]={"Auto","Flat","Dither","Wire"};
static char *speeds[3]={"Slow","Medium","Fast"};
static char *sizes[3]={"Small","Medium","Large"};
static void logtext(char *s)
{
 HFILE f;
 if(!benchmark&&!qaMode)return;
 f=_lopen(logpath,OF_WRITE);if(f==HFILE_ERROR)f=_lcreat(logpath,0);
 if(f!=HFILE_ERROR){_llseek(f,0L,2);_lwrite(f,s,lstrlen(s));_lclose(f);}
}
static int valid(int v,int lo,int hi,int fallback)
{return v>=lo&&v<=hi?v:fallback;}
static int drawingStyle(void)
{return style?style:((colors>0&&colors<=2)?2:1);}
static void viewport(HDC dc)
{
 int request[2],answer[6],n;
 viewX=viewY=0;viewW=screenW;viewH=screenH;
 request[0]=-1;request[1]=0;for(n=0;n<6;n++)answer[n]=0;
 /* Windows XT's documented read-only XY query. Unknown drivers return zero.
    Validate every field; never assume that a virtual desktop is all visible. */
 if(Escape(dc,0x5860,4,(LPSTR)request,(LPSTR)answer)>0&&
    answer[4]==screenW&&answer[5]==screenH&&answer[2]>=160&&answer[3]>=100&&
    answer[2]<=screenW&&answer[3]<=screenH&&answer[0]>=0&&answer[1]>=0&&
    answer[0]<=screenW-answer[2]&&answer[1]<=screenH-answer[3]){
  viewX=answer[0];viewY=answer[1];viewW=answer[2];viewH=answer[3];
 }
}
static void readSettings(void)
{
 style=valid(GetPrivateProfileInt("Cube","Style",0,ini),0,3,0);
 speed=valid(GetPrivateProfileInt("Cube","Speed",2,ini),1,3,2);
 cubeSize=valid(GetPrivateProfileInt("Cube","Size",2,ini),1,3,2);
}
static int saveSettings(void)
{
 char old[3][32], want[3][2], actual[32];
 char *key[3];int present[3],n,last=-1,ok=1;
 key[0]="Style";key[1]="Speed";key[2]="Size";
 want[0][0]=(char)('0'+selectedStyle);want[1][0]=(char)('0'+selectedSpeed);
 want[2][0]=(char)('0'+selectedSize);
 for(n=0;n<3;n++){
  want[n][1]=0;
  if(GetPrivateProfileString("Cube",key[n],"{absent}",old[n],32,ini)>=31)return 0;
  present[n]=1;
  if(!lstrcmp(old[n],"{absent}")){
   GetPrivateProfileString("Cube",key[n],"{absent2}",actual,32,ini);
   present[n]=lstrcmp(actual,"{absent2}")!=0;
  }
 }
 for(n=0;n<3;n++){
  last=n;
  if(!WritePrivateProfileString("Cube",key[n],want[n],"CUBE.INI")){ok=0;break;}
  GetPrivateProfileString("Cube",key[n],"?",actual,32,ini);
  if(lstrcmp(actual,want[n])){ok=0;break;}
 }
 if(!ok){
  for(n=0;n<=last;n++)WritePrivateProfileString("Cube",key[n],
     present[n]?old[n]:(LPSTR)NULL,"CUBE.INI");
  for(n=0;n<=last;n++){
   GetPrivateProfileString("Cube",key[n],"{absent}",actual,32,ini);
   if(lstrcmp(actual,old[n]))return -1;
  }
  return 0;
 }
 readSettings();return 1;
}
static int ownsScreen(void)
{
 HWND w;RECT r;
 if(GetActiveWindow()!=saver||GetFocus()!=saver||GetCapture()!=saver)return 0;
 for(w=GetWindow(saver,GW_HWNDPREV);w;w=GetWindow(w,GW_HWNDPREV))
  if(IsWindowVisible(w)&&!IsIconic(w)){
   GetWindowRect(w,&r);
   if(r.right>0&&r.bottom>0&&r.left<screenW&&r.top<screenH)return 0;
  }
 return 1;
}
static void restoreCursor(void)
{
 HCURSOR c=SetCursor(NULL);SetCursor(c==blankCursor?previousCursor:c);
 if(hidden){ShowCursor(TRUE);hidden=0;}
}
static void releaseDraw(void)
{
 int n;
 if(canvas){if(oldBitmap)SelectObject(canvas,oldBitmap);DeleteDC(canvas);canvas=NULL;}
 if(bitmap){DeleteObject(bitmap);bitmap=NULL;}oldBitmap=NULL;
 for(n=0;n<17;n++){
  if(shades[n])DeleteObject(shades[n]);shades[n]=NULL;
  if(solids[n])DeleteObject(solids[n]);solids[n]=NULL;
 }
 if(edge)DeleteObject(edge);edge=NULL;
}
static int initDraw(HWND w)
{
 /* At most 224x128 DDB pixels. No full-screen shadow or raw VRAM access. */
 static BYTE bayer[64]={
  0,32,8,40,2,34,10,42,48,16,56,24,50,18,58,26,
  12,44,4,36,14,46,6,38,60,28,52,20,62,30,54,22,
  3,35,11,43,1,33,9,41,51,19,59,27,49,17,57,25,
  15,47,7,39,13,45,5,37,63,31,55,23,61,29,53,21
 };
 BYTE bits[16];HBITMAP pattern;HDC dc;int x,y,n,ax,ay,mode=drawingStyle();
 dc=GetDC(w);if(!dc)return 0;
 viewport(dc);lastX=lastY=-1;
 cw=viewW-8;if(cw>224)cw=224;
 ch=viewH-8;if(ch>128)ch=128;
 if(cw<16||ch<16){ReleaseDC(w,dc);return 0;}
 /* ASPECTX/Y describe relative physical pixel dimensions in Win3 drivers. */
 ax=GetDeviceCaps(dc,ASPECTX);ay=GetDeviceCaps(dc,ASPECTY);
 if(ax<=0||ay<=0||ax>10000||ay>10000){ax=screenH*4;ay=screenW*3;}
 scaleX=cw*3/4;scaleY=(int)((long)scaleX*ax/ay);
 if(scaleY>ch*3/4){scaleY=ch*3/4;scaleX=(int)((long)scaleY*ay/ax);}
 if(scaleX<4)scaleX=4;if(scaleY<4)scaleY=4;
 scaleX=scaleX*(cubeSize+2)/5;scaleY=scaleY*(cubeSize+2)/5;
 /* The projected x radius is <=0.472*sx and y <=0.578*sy.
    Copy only that small rectangle, not its unused sizing envelope. */
 cw=scaleX+4;ch=scaleY*6/5+4;
 canvas=CreateCompatibleDC(dc);bitmap=CreateCompatibleBitmap(dc,cw,ch);
 edge=CreatePen(PS_SOLID,1,RGB(255,255,255));
 for(n=0;n<17;n++){
  if(mode==2){
   for(y=0;y<8;y++){
    bits[y*2]=bits[y*2+1]=0;
    for(x=0;x<8;x++)if((int)bayer[y*8+x]<n*4)bits[y*2]|=(BYTE)(128U>>x);
   }
   pattern=CreateBitmap(8,8,1,1,bits);
   if(pattern){shades[n]=CreatePatternBrush(pattern);DeleteObject(pattern);}
  }else if(mode==1){
   /* Grayscale flat illumination maps through the installed palette. */
   x=n*255/16;
   solids[n]=CreateSolidBrush(GetNearestColor(dc,RGB(x,x,x)));
  }
 }
 ReleaseDC(w,dc);
 if(!canvas||!bitmap||!edge)return 0;
 for(n=0;n<17;n++)if((mode==2&&!shades[n])||(mode==1&&!solids[n]))return 0;
 oldBitmap=SelectObject(canvas,bitmap);
 if(!oldBitmap)return 0;
 SetTextColor(canvas,RGB(0,0,0));SetBkColor(canvas,RGB(255,255,255));
 return 1;
}
static int render(void)
{
 POINT polygon[4];int n,j,x,y,mode=drawingStyle(),ok=1;
 HGDIOBJ oldpen,oldbrush;HDC dc;DWORD elapsed,sourcePixel,targetPixel,t=GetTickCount();char b[160];
 if(!running||!ownsScreen())return 0;
 if(blankCursor)SetCursor(blankCursor);
 elapsed=t-lastFrame;lastFrame=t;if(elapsed>500UL)elapsed=500UL;
 phaseTime+=elapsed*(DWORD)speed;
 while(phaseTime>=125UL){phaseTime-=125UL;phase++;}
 CubeFrame(phase,cw/2,ch/2,scaleX,scaleY,&frame);
 if(!PatBlt(canvas,0,0,cw,ch,BLACKNESS))ok=0;
 oldpen=SelectObject(canvas,edge);oldbrush=SelectObject(canvas,GetStockObject(NULL_BRUSH));
 if(mode==3){
  for(n=0;n<12;n++){
   j=CubeEdges[n][0];MoveTo(canvas,frame.point[j].x,frame.point[j].y);
   j=CubeEdges[n][1];if(!LineTo(canvas,frame.point[j].x,frame.point[j].y))ok=0;
  }
 }else for(n=0;n<6;n++)if(frame.visible[n]){
  for(j=0;j<4;j++){
   polygon[j].x=frame.point[CubeFaces[n][j]].x;polygon[j].y=frame.point[CubeFaces[n][j]].y;
  }
  SelectObject(canvas,mode==2?shades[frame.shade[n]]:solids[frame.shade[n]]);
  if(!Polygon(canvas,polygon,4))ok=0;
 }
 SelectObject(canvas,oldbrush);SelectObject(canvas,oldpen);
 dc=GetDC(saver);
 if(dc){
  viewport(dc);x=viewX+(viewW-cw)/2;y=viewY+(viewH-ch)/2;
  if(lastX>=0&&(lastX!=x||lastY!=y))
   if(!PatBlt(dc,lastX,lastY,cw,ch,BLACKNESS))ok=0;
  if(!BitBlt(dc,x,y,cw,ch,canvas,0,0,SRCCOPY))ok=0;
  if(qaMode&&frames==2){
   j=0;for(n=0;n<6;n++)if(frame.visible[n]){j=CubeFaces[n][0];break;}
   sourcePixel=GetPixel(canvas,frame.point[j].x,frame.point[j].y);
   targetPixel=GetPixel(dc,x+frame.point[j].x,y+frame.point[j].y);
   wsprintf(b,"PIXEL source=%lu target=%lu\r\n",sourcePixel,targetPixel);logtext(b);
   if(sourcePixel!=RGB(255,255,255)||targetPixel!=sourcePixel)ok=0;
  }
  lastX=x;lastY=y;
  ReleaseDC(saver,dc);
 }else ok=0;
 if(!ok)errors++;
 elapsed=GetTickCount()-t;drawTotal+=elapsed;if(elapsed>drawMax)drawMax=elapsed;
 frames++;
 if((benchmark||qaMode)&&(frames==1||frames==2||frames==16||frames==32)){
  wsprintf(b,"FRAME n=%d phase=%u style=%d errors=%d draw_ms=%lu\r\n",frames,phase,mode,errors,elapsed);logtext(b);
 }
 return ok;
}
static void stop(HWND w,char *reason)
{
 int back;char b[240];
 if(closing)return;
 closing=1;back=returnFocus&&GetActiveWindow()==w;
 running=draining=0;
 if(timerOn){KillTimer(w,1);timerOn=0;}
 KillTimer(w,2);
 if(GetCapture()==w)ReleaseCapture();restoreCursor();
 wsprintf(b,"END reason=%s frames=%d errors=%d draw_ms=%lu max_ms=%lu elapsed=%lu\r\n",
  (LPSTR)reason,frames,errors,drawTotal,drawMax,GetTickCount()-start);logtext(b);
 DestroyWindow(w);
 if(back&&IsWindow(previousActive)&&IsWindowVisible(previousActive)&&IsWindowEnabled(previousActive)){
  SetActiveWindow(previousActive);
  if(IsWindow(previousFocus)&&IsWindowEnabled(previousFocus)&&
    (previousFocus==previousActive||IsChild(previousActive,previousFocus)))SetFocus(previousFocus);
 }
}
static void wake(char *reason)
{
 if(!draining){draining=1;running=0;returnFocus=1;lstrcpy(wakeReason,reason);}
 lastInput=GetTickCount();
}
static int keysHeld(void)
{
 int n;
 for(n=3;n<256;n++)if(n!=VK_MBUTTON&&downKeys[n]){
  if(GetAsyncKeyState(n)&0x8000)return 1;downKeys[n]=0;
 }
 return 0;
}
static int input(HWND w,UINT m,WPARAM wp,LPARAM lp)
{
 int was;
 if(m>=WM_KEYFIRST&&m<=WM_KEYLAST){
  if(m==WM_KEYDOWN||m==WM_SYSKEYDOWN){if(wp<256)downKeys[wp]=1;wake("keyboard");}
  else if(m==WM_KEYUP||m==WM_SYSKEYUP){
   was=wp<256?initialKeys[wp]:0;
   if(wp<256){downKeys[wp]=initialKeys[wp]=0;}
   if(!was||GetTickCount()-armedAt>=250UL||draining)wake("key-release");
  }else wake("character");
  return 1;
 }
 if(m>=WM_MOUSEFIRST&&m<=WM_MOUSELAST){
  mouseHeld=wp&(MK_LBUTTON|MK_RBUTTON|MK_MBUTTON);
  if(m==WM_LBUTTONDOWN||m==WM_LBUTTONDBLCLK)mouseHeld|=MK_LBUTTON;
  if(m==WM_RBUTTONDOWN||m==WM_RBUTTONDBLCLK)mouseHeld|=MK_RBUTTON;
  if(m==WM_MBUTTONDOWN||m==WM_MBUTTONDBLCLK)mouseHeld|=MK_MBUTTON;
  if(m!=WM_MOUSEMOVE){mouseGesture=1;wake("mouse-button");}
  else if((int)LOWORD(lp)!=origin.x||(int)HIWORD(lp)!=origin.y)wake("mouse-move");
  return 1;
 }
 return 0;
}
static void drain(HWND w)
{
 MSG msg;DWORD quiet=mouseGesture?(DWORD)GetDoubleClickTime():110UL;
 if(!ownsScreen()){returnFocus=0;stop(w,"drain-owner-lost");return;}
 if(quiet<110UL)quiet=110UL;
 if(keysHeld()||mouseHeld){lastInput=GetTickCount();return;}
 while(PeekMessage(&msg,w,WM_KEYFIRST,WM_KEYLAST,PM_REMOVE))input(w,msg.message,msg.wParam,msg.lParam);
 while(PeekMessage(&msg,w,WM_MOUSEFIRST,WM_MOUSELAST,PM_REMOVE))input(w,msg.message,msg.wParam,msg.lParam);
 if(!keysHeld()&&!mouseHeld&&GetTickCount()-lastInput>=quiet)stop(w,wakeReason);
}
LONG FAR PASCAL CubeProc(HWND w,UINT m,WPARAM wp,LPARAM lp)
{
 PAINTSTRUCT ps;HDC dc;
 if(!closing&&input(w,m,wp,lp))return 0;
 switch(m){
 case WM_ERASEBKGND:return 1;
 case WM_PAINT:
  dc=BeginPaint(w,&ps);PatBlt(dc,ps.rcPaint.left,ps.rcPaint.top,
    ps.rcPaint.right-ps.rcPaint.left,ps.rcPaint.bottom-ps.rcPaint.top,BLACKNESS);
  EndPaint(w,&ps);if(running)render();return 0;
 case WM_SETCURSOR:if(running||draining)SetCursor(blankCursor);return 1;
 case WM_TIMER:
  if(wp==2){
   KillTimer(w,2);
   if(!SetTimer(w,1,110,NULL)){stop(w,"qa-resume-timer-failed");return 0;}
   timerOn=1;return 0;
  }
  if(wp!=1)return 0;
  if(draining){drain(w);return 0;}
  if(!running)return 0;
  if(!ownsScreen()){returnFocus=0;stop(w,"owner-lost");return 0;}
  if(!render()){stop(w,"draw-failed");return 0;}
  if(qaMode&&++qaFrames==2){
   /* A quiescent native frame lets a headless capture cross a scanout tick.
      The ordinary consumer renderer never enters this developer-only hold. */
   KillTimer(w,1);timerOn=0;
   if(!SetTimer(w,2,1500,NULL)){stop(w,"qa-hold-timer-failed");return 0;}
   logtext("QA CAPTURE READY\r\n");
  }
  if(qaMode&&qaFrames==12)PostMessage(qa,WM_USER+1,0,0L);
  if(benchmark&&frames>=32)stop(w,"benchmark");return 0;
 case WM_KILLFOCUS:
 case WM_CANCELMODE:
  if(running||draining){returnFocus=0;stop(w,"focus-or-cancel");}return 0;
 case WM_ACTIVATE:
  if(wp==WA_INACTIVE&&(running||draining)){returnFocus=0;stop(w,"deactivated");}return 0;
 case WM_ACTIVATEAPP:
  if(!wp&&(running||draining)){returnFocus=0;stop(w,"task-switch");}return 0;
 case WM_QUERYENDSESSION:shutdown=1;returnFocus=0;stop(w,"shutdown");return 1;
 case WM_ENDSESSION:shutdown=wp?1:shutdown;returnFocus=0;stop(w,"end-session");return 0;
 case WM_CLOSE:returnFocus=0;stop(w,"close");return 0;
 case WM_DESTROY:
  if(timerOn)KillTimer(w,1);KillTimer(w,2);timerOn=0;running=draining=0;
  if(GetCapture()==w)ReleaseCapture();restoreCursor();releaseDraw();saver=NULL;
  if(qaMode)PostMessage(qa,WM_USER+2,0,0L);
  else if(showConfig&&!shutdown&&config){ShowWindow(config,SW_SHOW);SetActiveWindow(config);}
  else PostQuitMessage(0);
  return 0;
 }
 return DefWindowProc(w,m,wp,lp);
}
static int startSaver(void)
{
 int n;char b[180];HDC dc;
 if(saver||GetCapture()||GetSysModalWindow())return 0;
 previousActive=GetActiveWindow();previousFocus=GetFocus();
 GetKeyboardState(initialKeys);
 for(n=0;n<256;n++){initialKeys[n]&=128;downKeys[n]=(BYTE)(initialKeys[n]?1:0);}
 GetCursorPos(&origin);armedAt=GetTickCount();
 previousCursor=SetCursor(NULL);SetCursor(previousCursor);
 running=draining=closing=returnFocus=mouseHeld=mouseGesture=0;
 if(initialKeys[VK_LBUTTON])mouseHeld|=MK_LBUTTON;
 if(initialKeys[VK_RBUTTON])mouseHeld|=MK_RBUTTON;
 if(initialKeys[VK_MBUTTON])mouseHeld|=MK_MBUTTON;
 frames=errors=qaFrames=0;phase=31;phaseTime=drawTotal=drawMax=0;start=lastFrame=GetTickCount();
 saver=CreateWindow("TandyCubeSaver","Rotating cube",WS_POPUP,0,0,screenW,screenH,NULL,NULL,instance,NULL);
 if(!saver)return 0;
 if(GetCapture()||GetSysModalWindow()||GetActiveWindow()!=previousActive){stop(saver,"startup-owner-changed");return 0;}
 ShowWindow(saver,SW_SHOW);SetActiveWindow(saver);SetFocus(saver);
 if(GetCapture()||GetSysModalWindow()){stop(saver,"startup-busy");return 0;}
 SetCapture(saver);
 if(!ownsScreen()){stop(saver,"activation-failed");return 0;}
 ScreenToClient(saver,&origin);UpdateWindow(saver);
 if(!initDraw(saver)){stop(saver,"allocation-failed");return 0;}
 if(!ownsScreen()){stop(saver,"startup-owner-lost");return 0;}
 dc=GetDC(saver);if(dc){PatBlt(dc,0,0,screenW,screenH,BLACKNESS);ReleaseDC(saver,dc);}
 ShowCursor(FALSE);hidden=1;SetCursor(blankCursor);
 running=1;
 if(!SetTimer(saver,1,110,NULL)){stop(saver,"timer-failed");return 0;}timerOn=1;
 wsprintf(b,"START width=%d height=%d colors=%d view=%d,%d,%d,%d canvas=%dx%d scale=%dx%d style=%d speed=%d size=%d free=%lu\r\n",
  screenW,screenH,colors,viewX,viewY,viewW,viewH,cw,ch,scaleX,scaleY,style,speed,cubeSize,GetFreeSpace(0));logtext(b);
 if(!render()){stop(saver,"first-draw-failed");return 0;}return 1;
}
static void labels(void)
{
 char b[40];
 wsprintf(b,"Style: %s",(LPSTR)styles[selectedStyle]);SetDlgItemText(config,ID_STYLE,b);
 wsprintf(b,"Speed: %s",(LPSTR)speeds[selectedSpeed-1]);SetDlgItemText(config,ID_SPEED,b);
 wsprintf(b,"Cube: %s",(LPSTR)sizes[selectedSize-1]);SetDlgItemText(config,ID_SIZE,b);
}
static int controls(HWND w,char *text,int x,int y,int width,int height,int id)
{
 HWND c=CreateWindow("BUTTON",text,WS_CHILD|WS_VISIBLE|WS_TABSTOP|BS_PUSHBUTTON,
  x,y,width,height,w,(HMENU)id,instance,NULL);
 if(c)SendMessage(c,WM_SETFONT,(WPARAM)GetStockObject(SYSTEM_FIXED_FONT),0L);
 return c!=NULL;
}
BOOL FAR PASCAL CubeCfgProc(HWND w,UINT m,WPARAM wp,LPARAM lp)
{
 PAINTSTRUCT ps;HDC dc;HFONT old;int saved;RECT r,c;
 switch(m){
 case WM_INITDIALOG:
  config=w;GetWindowRect(w,&r);GetClientRect(w,&c);
  dc=GetDC(w);if(dc){viewport(dc);ReleaseDC(w,dc);}
  SetWindowPos(w,NULL,viewX+(viewW-146)/2,viewY+(viewH-96)/2,
   144+r.right-r.left-c.right,94+r.bottom-r.top-c.bottom,SWP_NOZORDER);
  if(!controls(w,"X",124,1,16,12,ID_CLOSE)||
     !controls(w,"",6,16,132,15,ID_STYLE)||!controls(w,"",6,33,132,15,ID_SPEED)||
     !controls(w,"",6,50,132,15,ID_SIZE)||!controls(w,"&Save",6,72,60,18,ID_SAVE)||
     !controls(w,"&Preview",74,72,64,18,ID_PREVIEW)){EndDialog(w,-1);return TRUE;}
  selectedStyle=style;selectedSpeed=speed;selectedSize=cubeSize;labels();
  SetFocus(GetDlgItem(w,ID_STYLE));return FALSE;
 case WM_PAINT:
  dc=BeginPaint(w,&ps);old=SelectObject(dc,GetStockObject(SYSTEM_FIXED_FONT));
  SetBkMode(dc,TRANSPARENT);TextOut(dc,6,2,"Rotating cube",13);
  SelectObject(dc,old);EndPaint(w,&ps);return TRUE;
 case WM_COMMAND:
  if(wp==IDOK){
   HWND focused=GetFocus();
   if(!focused||GetParent(focused)!=w)return TRUE;
   wp=GetDlgCtrlID(focused);
  }
  if(wp==ID_CLOSE||wp==IDCANCEL){EndDialog(w,0);return TRUE;}
  if(wp==ID_STYLE){selectedStyle=(selectedStyle+1)%4;labels();return TRUE;}
  if(wp==ID_SPEED){selectedSpeed=selectedSpeed%3+1;labels();return TRUE;}
  if(wp==ID_SIZE){selectedSize=selectedSize%3+1;labels();return TRUE;}
  if(wp==ID_SAVE){
   saved=saveSettings();
   SetDlgItemText(w,ID_SAVE,saved>0?"Saved":saved==0?"Failed":"Check INI");return TRUE;
  }
  if(wp==ID_PREVIEW){
   if(!previewPending){previewPending=1;if(!SetTimer(w,2,55,NULL))previewPending=0;}
   return TRUE;
  }
  break;
 case WM_TIMER:
  if(wp==2&&previewPending){
   if(GetAsyncKeyState(VK_RETURN)&0x8000||GetAsyncKeyState(VK_SPACE)&0x8000||
     GetAsyncKeyState(VK_LBUTTON)&0x8000||GetCapture())return TRUE;
   KillTimer(w,2);previewPending=0;
   if(GetActiveWindow()!=w)return TRUE;
   style=selectedStyle;speed=selectedSpeed;cubeSize=selectedSize;
   /* Keep the dialog visible until startSaver has verified startup ownership. */
   if(!startSaver())SetDlgItemText(w,ID_PREVIEW,"Failed");
  }return TRUE;
 case WM_CLOSE:EndDialog(w,0);return TRUE;
 case WM_QUERYENDSESSION:return TRUE;
 case WM_ENDSESSION:if(wp){shutdown=1;EndDialog(w,0);}return TRUE;
 case WM_DESTROY:KillTimer(w,2);config=NULL;return TRUE;
 }
 return FALSE;
}
static void word(BYTE FAR **p,unsigned n){*(*p)++=(BYTE)n;*(*p)++=(BYTE)(n>>8);}
static int settings(void)
{
 HGLOBAL mem;BYTE FAR *p;DWORD units,flags;FARPROC proc;int result=-1;
 mem=GlobalAlloc(GMEM_MOVEABLE|GMEM_ZEROINIT,64);if(!mem)return -1;
 p=(BYTE FAR *)GlobalLock(mem);if(!p){GlobalFree(mem);return -1;}
 /* Caption-free compact dialog fits the 160x100 mode, including its border. */
 flags=WS_POPUP|WS_BORDER;word(&p,LOWORD(flags));word(&p,HIWORD(flags));*p++=0;
 units=GetDialogBaseUnits();word(&p,0);word(&p,0);word(&p,144*4/LOWORD(units));word(&p,94*8/HIWORD(units));
 *p++=0;*p++=0;*p=0;GlobalUnlock(mem);
 proc=MakeProcInstance((FARPROC)CubeCfgProc,instance);
 if(proc){result=DialogBoxIndirect(instance,mem,NULL,(DLGPROC)proc);FreeProcInstance(proc);}
 GlobalFree(mem);return result;
}
/* Optional native QA uses the actual renderer, window/input paths and GDI.
   It does not install, change CUBE.INI or require a raw framebuffer format. */
LONG FAR PASCAL CubeQAProc(HWND w,UINT m,WPARAM wp,LPARAM lp)
{
 PAINTSTRUCT ps;HDC dc;RECT r;char b[160];
 switch(m){
 case WM_PAINT:
  dc=BeginPaint(w,&ps);GetClientRect(w,&r);FillRect(dc,&r,GetStockObject(WHITE_BRUSH));
  TextOut(dc,2,2,"CUBE QA DESKTOP",15);EndPaint(w,&ps);return 0;
 case WM_USER:
  style=qaStep%3+1;UpdateWindow(w);
  if(!startSaver()){logtext("QA START FAIL\r\n");DestroyWindow(w);}return 0;
 case WM_USER+1:
  if(qaStep==0){SendMessage(saver,WM_KEYDOWN,VK_ESCAPE,0L);SendMessage(saver,WM_CHAR,27,0L);SendMessage(saver,WM_KEYUP,VK_ESCAPE,0L);}
  else if(qaStep==1){SendMessage(saver,WM_LBUTTONDOWN,MK_LBUTTON,0L);SetTimer(w,3,440,NULL);}
  else if(qaStep==2)SendMessage(saver,WM_MOUSEMOVE,0,MAKELONG(origin.x+1,origin.y));
  else if(qaStep==3)SetActiveWindow(w);
  else if(qaStep==4)SendMessage(saver,WM_CLOSE,0,0L);
  else if(qaStep==5)SetCapture(w);
  return 0;
 case WM_TIMER:
  if(wp==3){KillTimer(w,3);logtext(saver&&draining&&GetCapture()==saver?"QA HELD PASS\r\n":"QA HELD FAIL\r\n");
   SendMessage(saver,WM_LBUTTONUP,0,0L);}return 0;
 case WM_USER+2:
  if(GetCapture()==w)ReleaseCapture();UpdateWindow(w);
  wsprintf(b,"QA step=%d frames=%d errors=%d leaks=%d capture=%d resources=%d\r\n",
   qaStep,frames,errors,qaLeaks,GetCapture()!=NULL,canvas!=NULL||bitmap!=NULL||edge!=NULL);logtext(b);
  if(errors||frames<12||qaLeaks||GetCapture()||canvas||bitmap||edge){logtext("QA FAIL\r\n");DestroyWindow(w);return 0;}
  if(++qaStep<6)PostMessage(w,WM_USER,0,0L);
  else{qaDone=1;logtext("QA DONE PASS\r\n");DestroyWindow(w);}return 0;
 case WM_KEYDOWN:case WM_KEYUP:case WM_SYSKEYDOWN:case WM_CHAR:
 case WM_LBUTTONDOWN:case WM_LBUTTONUP:qaLeaks++;return 0;
 case WM_DESTROY:PostQuitMessage(0);return 0;
 }
 return DefWindowProc(w,m,wp,lp);
}
int PASCAL WinMain(HINSTANCE inst,HINSTANCE prev,LPSTR cmd,int show)
{
 WNDCLASS wc;MSG msg;HDC dc;HFILE f;int n,i,key,value;char b[32];
 instance=inst;
 if(prev||FindWindow("TandyCubeSaver",NULL))return 8;
 GetWindowsDirectory(ini,sizeof(ini));if(lstrlen(ini)>128)return 1;lstrcat(ini,"\\CUBE.INI");readSettings();
 GetModuleFileName(inst,logpath,sizeof(logpath));n=lstrlen(logpath);
 for(i=n-1;i>=0&&logpath[i]!='\\'&&logpath[i]!=':';i--);logpath[i+1]=0;lstrcat(logpath,"CUBE.LOG");
 showConfig=!cmd[0];
 for(i=0;cmd[i];i++)if((i==0||cmd[i-1]==' ')&&cmd[i]=='/'){
  key=cmd[i+1];if(key>='a'&&key<='z')key-=32;
  if((!cmd[i+2]||cmd[i+2]==' ')){
   if(key=='C')showConfig=1;if(key=='S')showConfig=0;
   if(key=='F')style=1;if(key=='D')style=2;if(key=='W')style=3;
   if(key=='T')benchmark=1;if(key=='Q')qaMode=1;
  }
  if((key=='V'||key=='Z')&&cmd[i+2]>='1'&&cmd[i+2]<='3'&&(!cmd[i+3]||cmd[i+3]==' ')){
   value=cmd[i+2]-'0';if(key=='V')speed=value;else cubeSize=value;
  }
 }
 if(benchmark||qaMode){showConfig=0;f=_lcreat(logpath,0);if(f!=HFILE_ERROR)_lclose(f);}
 screenW=GetSystemMetrics(SM_CXSCREEN);screenH=GetSystemMetrics(SM_CYSCREEN);
 if(screenW<160||screenH<100||screenW>4096||screenH>4096)return 2;
 dc=GetDC(NULL);if(!dc)return 3;colors=GetDeviceCaps(dc,NUMCOLORS);ReleaseDC(NULL,dc);
 for(n=0;n<128;n++){cursorAnd[n]=255;cursorXor[n]=0;}
 blankCursor=CreateCursor(inst,0,0,32,32,cursorAnd,cursorXor);if(!blankCursor)return 4;
 wc.style=0;wc.lpfnWndProc=CubeProc;wc.cbClsExtra=wc.cbWndExtra=0;wc.hInstance=inst;
 wc.hIcon=NULL;wc.hCursor=NULL;wc.hbrBackground=NULL;wc.lpszMenuName=NULL;wc.lpszClassName="TandyCubeSaver";
 if(!RegisterClass(&wc)){DestroyCursor(blankCursor);return 5;}
 wc.lpfnWndProc=CubeQAProc;wc.lpszClassName="CubeQA";
 if(!RegisterClass(&wc)){DestroyCursor(blankCursor);return 5;}
 if(showConfig){settings();}
 else{
  if(qaMode){
   qa=CreateWindow("CubeQA","Cube QA",WS_POPUP,0,0,screenW,screenH,NULL,NULL,inst,NULL);
   if(!qa){DestroyCursor(blankCursor);return 6;}ShowWindow(qa,SW_SHOW);SetActiveWindow(qa);SetFocus(qa);PostMessage(qa,WM_USER,0,0L);
  }else if(!startSaver()){DestroyCursor(blankCursor);return 7;}
  while(GetMessage(&msg,NULL,0,0))DispatchMessage(&msg);
 }
 DestroyCursor(blankCursor);wsprintf(b,"QUIT clean qa=%d\r\n",qaDone);logtext(b);
 return errors||(qaMode&&!qaDone)?9:0;
}
