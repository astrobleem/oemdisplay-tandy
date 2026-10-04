#define WINVER 0x0300
#include <windows.h>
extern unsigned FAR PASCAL BiosMode(void);
static HFILE logFile;
static HDC dc;
static int width,seq=0;
static HPEN pen;
static HBRUSH white,yellow,black;
static void line(char *key,DWORD value){char b[100],d[12];int n=0,k=0;while(*key)b[n++]=*key++;b[n++]='=';do{d[k++]=(char)('0'+value%10);value/=10;}while(value);while(k)b[n++]=d[--k];b[n++]='\r';b[n++]='\n';_lwrite(logFile,b,n);}
static void flush(void){_lclose(logFile);logFile=_lopen("C:\\OUTPUT.LOG",OF_WRITE);_llseek(logFile,0L,2);}
static void clear(void){RECT r;r.left=0;r.top=0;r.right=width;r.bottom=200;line("CLEAR_SUCCESS",FillRect(dc,&r,white)!=0);}
static void dump(void){HFILE h;char n[]="C:\\OP00.BIN";n[5]=(char)('0'+seq/10);n[6]=(char)('0'+seq%10);h=_lcreat(n,0);line("DUMP_CREATED",h!=HFILE_ERROR);if(h!=HFILE_ERROR){line("DUMP_BYTES",_lwrite(h,(const void _huge *)0xb8000000L,0x8000U));_lclose(h);}}
static void lines(int kind,int count){DWORD t0,t1,mask=0;int i,ok=0,result=0;POINT p[2];seq++;clear();SelectObject(dc,pen);line("STAGE",seq);line("KIND",kind);line("COUNT",count);flush();t0=GetTickCount();
 for(i=0;i<count;i++){
  if(kind==1){p[0].x=10;p[0].y=24+i%8;p[1].x=64;p[1].y=p[0].y;}
  if(kind==2){p[0].x=10+i*4;p[0].y=64;p[1].x=64+i*4;p[1].y=118;}
  if(kind==3){p[0].x=width/2+i*3;p[0].y=48;p[1].x=p[0].x;p[1].y=102;}
  result=Polyline(dc,p,2);if(result){ok++;mask|=1L<<i;}
 }
 t1=GetTickCount();line("T0_MS",t0);line("T1_MS",t1);line("ELAPSED_MS",t1-t0);line("API_SUCCESSES",ok);line("SUCCESS_MASK",mask);line("LAST_RESULT",result);dump();flush();
}
static void scene(void){DWORD t0,t1;int x=width/2-6,y=64,result;HBRUSH old;seq++;clear();SelectObject(dc,pen);old=SelectObject(dc,yellow);line("STAGE",seq);line("KIND",4);line("COUNT",1);line("ELLIPSE_LEFT",x);line("ELLIPSE_TOP",y);line("ELLIPSE_WIDTH",12);line("ELLIPSE_HEIGHT",12);flush();t0=GetTickCount();
 result=Ellipse(dc,x,y,x+12,y+12);
 t1=GetTickCount();SelectObject(dc,old);line("T0_MS",t0);line("T1_MS",t1);line("ELAPSED_MS",t1-t0);line("API_SUCCESSES",result!=0);line("SUCCESS_MASK",result!=0);line("LAST_RESULT",result);line("ELLIPSE_CENTER_READBACK",GetPixel(dc,width/2,y+6));dump();flush();
}
int PASCAL WinMain(HINSTANCE inst,HINSTANCE prev,LPSTR cmd,int show){int hide=0,c,num;HCURSOR oldcur;HPEN oldpen;logFile=_lcreat("C:\\OUTPUT.LOG",0);if(logFile==HFILE_ERROR)return 1;dc=GetDC(NULL);width=GetSystemMetrics(0);num=GetDeviceCaps(dc,NUMCOLORS);line("VERSION",2);line("SCREEN_WIDTH",width);line("SCREEN_HEIGHT",GetSystemMetrics(1));line("BIOS_MODE",BiosMode()&255);line("NUMCOLORS",num);line("TICK_RESOLUTION_APPROX_MS",55);line("SMALL_ELLIPSE_PROBE_NOT_COOKIE_APP",1);
 if(GetSystemMetrics(1)!=200||!((width==320&&num==16)||(width==640&&num==4))){line("WRONG_MODE",1);_lclose(logFile);ReleaseDC(NULL,dc);return 2;}
 white=GetStockObject(WHITE_BRUSH);black=GetStockObject(BLACK_BRUSH);yellow=CreateSolidBrush(RGB(255,255,0));pen=CreatePen(PS_SOLID,1,RGB(0,0,0));line("BRUSH_CREATED",yellow!=NULL);line("PEN_CREATED",pen!=NULL);if(!yellow||!pen){line("OBJECT_FAILURE",1);_lclose(logFile);ReleaseDC(NULL,dc);return 3;}
 oldpen=SelectObject(dc,pen);SetMapMode(dc,MM_TEXT);SetROP2(dc,R2_COPYPEN);SetBkMode(dc,OPAQUE);SetBkColor(dc,RGB(255,255,255));do{c=ShowCursor(FALSE);hide++;}while(c>=0&&hide<32);oldcur=SetCursor(NULL);line("CURSOR_HIDDEN",1);flush();
 lines(1,16);lines(2,4);lines(3,4);scene();line("COMPLETE",1);_lclose(logFile);SelectObject(dc,oldpen);DeleteObject(pen);DeleteObject(yellow);ReleaseDC(NULL,dc);SetCursor(oldcur);while(hide-->0)ShowCursor(TRUE);return 0;}
