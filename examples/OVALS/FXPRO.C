/* New five-scene Tandy320 native GDI comparison; not saver lifecycle/timing. */
#define WINVER 0x0300
#include <windows.h>
#include "OVALFX.H"
typedef WORD(FAR PASCAL *Counter)(void);
typedef int(FAR PASCAL *Factory)(int,const LOGPEN FAR *,BYTE FAR *);
static Counter counter;static Factory factory;static HFILE logFile,rawFile;static BYTE FAR *physical;
static LOGPEN logical;static COLORREF colors[8];static int cases,failures;
static void line(char *s){UINT n=(UINT)lstrlen(s);if(_lwrite(logFile,s,n)!=n)failures++;}
static int put(const void FAR *p,UINT n){return _lwrite(rawFile,(LPCSTR)p,n)==n;}
static int run(unsigned n,BYTE value){return put((const void FAR *)&n,2)&&put((const void FAR *)&value,1);}
static int capture(int phase){BYTE FAR *v=(BYTE FAR *)0xb8000000UL;unsigned n,length=0;BYTE last=0;WORD header[2];header[0]=(WORD)cases;header[1]=(WORD)phase;if(!put((const void FAR *)header,4))return 0;
 for(n=0;n<32768U;n++){if(length&&v[n]!=last){if(!run(length,last))return 0;length=0;}last=v[n];length++;}return !length||run(length,last);}
static int realize(int color,int width,char *text){unsigned n;static char hex[]="0123456789abcdef";
 for(n=0;n<48;n++)physical[n]=0xa5;logical.lopnStyle=PS_SOLID;logical.lopnWidth.x=width;logical.lopnWidth.y=0;logical.lopnColor=colors[color];
 if(factory(1,(const LOGPEN FAR *)&logical,(BYTE FAR *)0)!=16||factory(1,(const LOGPEN FAR *)&logical,physical+16)!=16)return 0;
 for(n=0;n<16;n++)if(physical[n]!=0xa5||physical[n+32]!=0xa5)return 0;
 for(n=0;n<16;n++){text[2*n]=hex[physical[16+n]>>4];text[2*n+1]=hex[physical[16+n]&15];}text[32]=0;return 1;}
static int draw(HDC dc,const FXOval FAR *o){POINT pts[33];int n,x,y;
 if(!o->angle)return Ellipse(dc,o->cx-o->rx,o->cy-o->ry,o->cx+o->rx,o->cy+o->ry);
 for(n=0;n<=32;n++){fxVertex(o,n,&x,&y);pts[n].x=x;pts[n].y=y;}return Polyline(dc,(POINT FAR *)pts,33);
}
static unsigned vertexHash(const FXOval FAR *o){int n,x,y;unsigned sum=0;
 for(n=0;n<=32;n++){fxVertex(o,n,&x,&y);sum=sum*33U+(unsigned)x;sum=sum*33U+(unsigned)y;}return sum;
}
static void scene(HDC dc,HBRUSH blue,int effect,int phase,int index,int count){RECT all;FXOval shape;int saved,ret,resync,erased,resync2,color;HPEN pen;WORD accepted,after,eraseAccepted,after2;char row[360],prefix[33];
 fxShape(effect,phase,index,count,320,200,&shape);color=shape.color;
 if(!realize(color,1,prefix)){failures++;return;}pen=CreatePen(PS_SOLID,1,colors[color]);if(!pen){failures++;return;}
 all.left=all.top=0;all.right=320;all.bottom=200;SetROP2(dc,R2_COPYPEN);if(!FillRect(dc,&all,blue)){failures++;return;}
 saved=SaveDC(dc);if(!saved||!SelectObject(dc,pen)||!SelectObject(dc,GetStockObject(NULL_BRUSH))||!SetROP2(dc,R2_XORPEN)||!SetBkMode(dc,OPAQUE)){failures++;return;}
 (void)counter();ret=draw(dc,(const FXOval FAR *)&shape);accepted=counter();
 if(!RestoreDC(dc,saved)||!capture(0)){failures++;return;}resync=BitBlt(dc,0,0,1,1,dc,0,0,SRCCOPY);after=counter();
 if(!resync||!capture(1)||!ret){failures++;return;}
 saved=SaveDC(dc);if(!saved||!SelectObject(dc,pen)||!SelectObject(dc,GetStockObject(NULL_BRUSH))||!SetROP2(dc,R2_XORPEN)||!SetBkMode(dc,OPAQUE)){failures++;return;}
 (void)counter();erased=draw(dc,(const FXOval FAR *)&shape);eraseAccepted=counter();
 if(!RestoreDC(dc,saved)||!capture(2)){failures++;return;}resync2=BitBlt(dc,0,0,1,1,dc,0,0,SRCCOPY);after2=counter();
 if(!resync2||!capture(3)||!erased||!DeleteObject(pen)||factory(-1,(const LOGPEN FAR *)&logical,physical+16)!=1){failures++;return;}
 wsprintf(row,"CASE=%d EFFECT=%d PHASE=%d INDEX=%d COUNT=%d CX=%d CY=%d RX=%d RY=%d ANGLE=%d COLOR=%d AX=%d AY=%d HASH=%u RGB=%lu PREFIX=%s RET=%d ERASE_RET=%d ACCEPTED=%u ERASE_ACCEPTED=%u RESYNC_ACCEPTED=%u RESYNC2_ACCEPTED=%u RESYNC=%d RESYNC2=%d\r\n",cases,effect,phase,index,count,shape.cx,shape.cy,shape.rx,shape.ry,shape.angle,color,shape.aspectX,shape.aspectY,vertexHash((const FXOval FAR *)&shape),colors[color],(LPSTR)prefix,ret,erased,accepted,eraseAccepted,after,after2,resync,resync2);line(row);cases++;
}
int PASCAL WinMain(HINSTANCE inst,HINSTANCE prev,LPSTR cmd,int show){HDC dc;HMODULE display;HGLOBAL mem;HBRUSH blue;int quick,n,e,p,i,ns,idx,hides=0;char row[180];
 if(sizeof(unsigned)!=2||sizeof(LOGPEN)!=10||sizeof(FXOval)!=16||sizeof(POINT)!=4||GetWinFlags()&WF_PMODE||*((volatile BYTE FAR *)0x00400049UL)!=9||*((volatile BYTE FAR *)0xf000fffeUL)==0xfdU)return 2;
 quick=cmd[0]=='/'&&(cmd[1]=='Q'||cmd[1]=='q')&&cmd[2]==0;if(cmd[0]&&!quick)return 3;
 display=GetModuleHandle("DISPLAY");if(!display)return 4;counter=(Counter)GetProcAddress(display,MAKEINTRESOURCE(504));factory=(Factory)GetProcAddress(display,MAKEINTRESOURCE(502));if(!counter||!factory)return 5;
 dc=GetDC(NULL);if(!dc||GetDeviceCaps(dc,HORZRES)!=320||GetDeviceCaps(dc,VERTRES)!=200||GetDeviceCaps(dc,NUMCOLORS)!=16||GetDeviceCaps(dc,CURVECAPS)!=8)return 6;
 mem=GlobalAlloc(GMEM_MOVEABLE,48UL);if(!mem)return 7;physical=(BYTE FAR *)GlobalLock(mem);if(!physical||LOWORD((DWORD)physical)>65488U)return 8;
 colors[0]=RGB(85,255,255);colors[1]=RGB(255,85,255);colors[2]=RGB(255,255,85);colors[3]=RGB(85,255,85);colors[4]=RGB(85,85,255);colors[5]=RGB(255,85,85);colors[6]=RGB(255,255,255);colors[7]=RGB(170,170,170);
 logFile=_lcreat("FXPRO.LOG",0);rawFile=_lcreat("FXPRO.RLE",0);if(logFile==HFILE_ERROR||rawFile==HFILE_ERROR)return 9;
 blue=CreateSolidBrush(RGB(0,0,255));if(!blue)return 10;SetMapMode(dc,MM_TEXT);SetWindowOrg(dc,0,0);SetViewportOrg(dc,0,0);
 do{n=ShowCursor(FALSE);hides++;}while(n>=0&&hides<16);if(n>=0){while(hides--)ShowCursor(TRUE);return 11;}
 wsprintf(row,"VERSION=2 EFFECTS=5 DENSITY=16 PHASES=%d GRID=%s CAPS=8 FRAME_BYTES=32768 FRAMES_PER_CASE=4\r\n",quick?4:8,(LPSTR)(quick?"Q":"FULL"));line(row);
 for(e=0;e<5&&!failures;e++){ns=fxCount(e,16);
  for(p=0;p<(quick?4:8)&&!failures;p++)for(i=0;i<(quick?(e==4?5:3):ns)&&!failures;i++){
   idx=quick?(e==4?(i<4?i:ns-1):(i==0?0:i==1?ns/2:ns-1)):i;
   scene(dc,blue,e,p*(quick?16:8),idx,ns);
  }
 }
 wsprintf(row,"CASES=%d FAILURES=%d\r\n%s\r\n",cases,failures,(LPSTR)(failures?"FAILED=1":"COMPLETE=1"));line(row);_lclose(rawFile);_lclose(logFile);while(hides--)ShowCursor(TRUE);DeleteObject(blue);ReleaseDC(NULL,dc);GlobalUnlock(mem);GlobalFree(mem);InvalidateRect(GetDesktopWindow(),(RECT FAR *)0,TRUE);return failures?1:0;
}
