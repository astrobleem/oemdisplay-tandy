#define WINVER 0x0300
#include <windows.h>
#include "CUBECORE.H"
#include "CUBERECT.H"
static HWND window;
static HDC display,source,target;
static HBITMAP sourceBitmap,targetBitmap,oldSource,oldTarget;
static HPEN pen;
static int errors,ran,hidden;
static HCURSOR previousCursor;
static char message[200];
static void line(char *text)
{
 HFILE f=_lopen("C:\\BLTPROF.LOG",OF_WRITE);
 if(f==HFILE_ERROR)f=_lcreat("C:\\BLTPROF.LOG",0);
 if(f!=HFILE_ERROR){_llseek(f,0L,2);_lwrite(f,text,lstrlen(text));_lclose(f);}
}
static void image(int mono,CBOX *dirty)
{
 CFRAME frame,previous;CBOX old,current,unused;POINT poly[4];HBRUSH brush,oldBrush;
 HGDIOBJ oldPen;BITMAP info;int i,j,shade;
 sourceBitmap=mono?CreateBitmap(49,95,1,1,NULL):CreateCompatibleBitmap(display,49,95);
 targetBitmap=CreateCompatibleBitmap(display,49,95);
 if(!sourceBitmap||!targetBitmap){errors++;line("FAIL bitmap allocation\r\n");return;}
 GetObject(sourceBitmap,sizeof(info),(LPSTR)&info);wsprintf(message,"BITMAP mono=%d planes=%d bits=%d width_bytes=%d\r\n",mono,info.bmPlanes,info.bmBitsPixel,info.bmWidthBytes);line(message);
 oldSource=SelectObject(source,sourceBitmap);oldTarget=SelectObject(target,targetBitmap);
 SetTextColor(source,RGB(0,0,0));SetBkColor(source,RGB(255,255,255));
 PatBlt(source,0,0,49,95,BLACKNESS);PatBlt(target,0,0,49,95,BLACKNESS);
 CubeFrame(47,24,47,45,76,&previous);CubeFrame(55,24,47,45,76,&frame);
 CubeDirtyBounds(&previous,49,95,&unused,0,&old,&current);
 CubeDirtyBounds(&frame,49,95,&old,1,&current,dirty);
 oldPen=SelectObject(source,pen);oldBrush=SelectObject(source,GetStockObject(NULL_BRUSH));
 for(i=0;i<6;i++)if(frame.visible[i]){
  for(j=0;j<4;j++){poly[j].x=frame.point[CubeFaces[i][j]].x;poly[j].y=frame.point[CubeFaces[i][j]].y;}
  shade=frame.shade[i]*255/16;
  brush=CreateSolidBrush(mono?RGB(255,255,255):GetNearestColor(display,RGB(shade,shade,shade)));
  SelectObject(source,brush);if(!Polygon(source,poly,4))errors++;
  SelectObject(source,oldBrush);DeleteObject(brush);
 }
 SelectObject(source,oldBrush);SelectObject(source,oldPen);
}
static void sample(char *kind,int mono,int rect,int number,HDC dst,HDC src,int calls,CBOX *r)
{
 DWORD begin,end;int i,x=r->left,y=r->top,w=r->right-x,h=r->bottom-y;
 begin=GetTickCount();
 for(i=0;i<calls;i++)if(!BitBlt(dst,x,y,w,h,src,x,y,SRCCOPY))errors++;
 end=GetTickCount();
 wsprintf(message,"SAMPLE kind=%s mono=%d rect=%d sample=%d calls=%d x=%d y=%d w=%d h=%d ms=%lu errors=%d\r\n",(LPSTR)kind,mono,rect,number,calls,x,y,w,h,end-begin,errors);line(message);
}
static void run(void)
{
 int mono,rep,k;CBOX full,dirty,pixel;CBOX *rects[2];COLORREF before,after,shown;
 full.left=full.top=0;full.right=49;full.bottom=95;
 pixel.left=pixel.top=24;pixel.right=pixel.bottom=25;
 rects[0]=&full;rects[1]=&dirty;
 SetTextColor(display,RGB(0,0,0));SetBkColor(display,RGB(255,255,255));
 SetTextColor(target,RGB(0,0,0));SetBkColor(target,RGB(255,255,255));
 for(mono=0;mono<2;mono++){
  image(mono,&dirty);if(errors)return;
  for(k=0;k<2;k++)for(rep=0;rep<3;rep++){
   /* Alternating order separates memory raster copying from display presentation. */
   if(rep&1){sample("display",mono,k,rep,display,source,8,rects[k]);sample("memory",mono,k,rep,target,source,128,rects[k]);}
   else{sample("memory",mono,k,rep,target,source,128,rects[k]);sample("display",mono,k,rep,display,source,8,rects[k]);}
  }
  before=GetPixel(source,24,47);after=GetPixel(target,24,47);shown=GetPixel(display,24,47);
  wsprintf(message,"READBACK mono=%d source=%lu target=%lu display=%lu\r\n",mono,before,after,shown);line(message);
  if(before!=after||before!=shown)errors++;
  SelectObject(source,oldSource);SelectObject(target,oldTarget);DeleteObject(sourceBitmap);DeleteObject(targetBitmap);sourceBitmap=targetBitmap=NULL;
 }
 /* Current TR5 documents identity SRCCOPY as synchronous resynchronization.
    This is a flush/presentation proxy, including GDI dispatch, not a direct
    timing of an unexported driver routine. Its behavior is measured here. */
 for(rep=0;rep<3;rep++){
  sample("display-identity-full",0,0,rep,display,display,8,&full);
  sample("display-identity-pixel",0,1,rep,display,display,8,&pixel);
 }
 wsprintf(message,"DONE errors=%d\r\n",errors);line(message);
}
LONG FAR PASCAL ProbeProc(HWND w,UINT m,WPARAM wp,LPARAM lp)
{
 PAINTSTRUCT ps;HDC dc;
 if(m==WM_PAINT){dc=BeginPaint(w,&ps);PatBlt(dc,0,0,160,200,BLACKNESS);EndPaint(w,&ps);return 0;}
 if(m==WM_SETCURSOR){SetCursor(NULL);return 1;}
 if(m==WM_USER&&!ran){ran=1;run();DestroyWindow(w);return 0;}
 if(m==WM_DESTROY){PostQuitMessage(0);return 0;}
 return DefWindowProc(w,m,wp,lp);
}
int PASCAL WinMain(HINSTANCE inst,HINSTANCE prev,LPSTR cmd,int show)
{
 WNDCLASS wc;MSG msg;FARPROC blt;HFILE f;
 f=_lcreat("C:\\BLTPROF.LOG",0);if(f==HFILE_ERROR)return 1;_lclose(f);
 if(GetSystemMetrics(0)!=160||GetSystemMetrics(1)!=200)return 2;
 display=GetDC(NULL);source=CreateCompatibleDC(display);target=CreateCompatibleDC(display);pen=CreatePen(PS_SOLID,1,RGB(255,255,255));
 if(!display||!source||!target||!pen)return 3;
 do{hidden++;}while(ShowCursor(FALSE)>=0&&hidden<32);previousCursor=SetCursor(NULL);
 blt=GetProcAddress(GetModuleHandle("DISPLAY"),"BITBLT");
 wsprintf(message,"READY display_module=%u bitblt_cs=%u bitblt_ip=%u\r\n",GetModuleHandle("DISPLAY"),HIWORD((DWORD)blt),LOWORD((DWORD)blt));line(message);
 wc.style=0;wc.lpfnWndProc=ProbeProc;wc.cbClsExtra=wc.cbWndExtra=0;wc.hInstance=inst;wc.hIcon=NULL;wc.hCursor=NULL;wc.hbrBackground=GetStockObject(BLACK_BRUSH);wc.lpszMenuName=NULL;wc.lpszClassName="BltProfile";
 if(!RegisterClass(&wc))return 4;
 window=CreateWindow("BltProfile","Private BitBlt profile",WS_POPUP,0,0,160,200,NULL,NULL,inst,NULL);
 ShowWindow(window,SW_SHOW);UpdateWindow(window);SetActiveWindow(window);SetFocus(window);PostMessage(window,WM_USER,0,0L);
 while(GetMessage(&msg,NULL,0,0)){TranslateMessage(&msg);DispatchMessage(&msg);}
 DeleteDC(source);DeleteDC(target);DeleteObject(pen);ReleaseDC(NULL,display);SetCursor(previousCursor);while(hidden-->0)ShowCursor(TRUE);
 line("CLEAN stopped\r\n");ExitWindows(0L,0);return errors?5:0;
}
