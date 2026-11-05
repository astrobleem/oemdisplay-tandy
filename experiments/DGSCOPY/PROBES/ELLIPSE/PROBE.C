#define WINVER 0x0300
#include <windows.h>
#include <string.h>
typedef WORD (FAR PASCAL *COUNTERPROC)(void);
static COUNTERPROC getCount;
static HFILE logf;static HDC dc;static int w,h,seq,profile;static BYTE chunk[8000];
static COLORREF colors[8]={0L,0xffL,0xff00L,0xff0000L,0xffffL,0xff00ffL,0xffff00L,0xffffffL};
static void line(char *key,long value){char b[120];wsprintf(b,"%s=%ld\r\n",(LPSTR)key,value);_lwrite(logf,b,lstrlen(b));}
static void text(char *s){_lwrite(logf,s,lstrlen(s));}
static void flush(void){_lclose(logf);logf=_lopen("C:\\PROBE.LOG",OF_WRITE);_llseek(logf,0L,2);}
static void pump(unsigned ms){MSG m;DWORD t=GetTickCount();while(GetTickCount()-t<ms){while(PeekMessage(&m,NULL,0,0,PM_REMOVE)){TranslateMessage(&m);DispatchMessage(&m);}}}
static void clear(void){RECT r;r.left=r.top=0;r.right=w;r.bottom=h;SelectClipRgn(dc,NULL);SetROP2(dc,R2_COPYPEN);FillRect(dc,&r,GetStockObject(WHITE_BRUSH));}
static void dump(char *stage){char name[32],b[100];unsigned at,total,n;HFILE f;BYTE FAR *v;
 line("ADMISSIONS",getCount?getCount():-1);
 wsprintf(b,"STAGE=%s\r\n",(LPSTR)stage);text(b);line("SEQ",seq);
 wsprintf(name,"C:\\F%02d.BIN",seq++);f=_lcreat(name,0);
 total=profile==2?64000U:32768U;v=(BYTE FAR *)(profile==2?0xa0000000L:0xb8000000L);
 for(at=0;at<total;){n=total-at;if(n>8000)n=8000;
  _asm pushf
  _asm cli
  _fmemcpy((LPSTR)chunk,(LPSTR)(v+at),n);
  _asm popf
  if(_lwrite(f,(LPSTR)chunk,n)!=n)line("WRITE_ERROR",1);at+=n;
 }_lclose(f);flush();
}
static void ell(int style,int pw,int solid,int rop,int clipped){int i;HPEN p,op;HBRUSH b,ob;HRGN r;DWORD t=GetTickCount();
 getCount();clear();if(clipped){r=CreateRectRgn(11,17,w-9,h-13);SelectClipRgn(dc,r);DeleteObject(r);}SetROP2(dc,rop);
 for(i=0;i<8;i++){p=CreatePen(PS_SOLID,pw,colors[i]);b=solid?CreateSolidBrush(colors[(i+2)&7]):GetStockObject(NULL_BRUSH);
  op=SelectObject(dc,p);ob=SelectObject(dc,b);
  if(style==1)Ellipse(dc,-5+i*3,3+i*3,w+4-i*4,h-3-i*4);
  else if(style==2)Ellipse(dc,i*12+2,8+i*3,i*12+3+(i%3),9+i*3+(i%4));
  else Ellipse(dc,3+i*(w/10),5+i*3,3+i*(w/10)+w/4,40+i*7);
  SelectObject(dc,op);SelectObject(dc,ob);DeleteObject(p);if(solid)DeleteObject(b);
 }line("DRAW_MS",GetTickCount()-t);SelectClipRgn(dc,NULL);
}

static void kernels(void){int trial,i;HPEN p,op;HBRUSH ob;DWORD start,elapsed;WORD count;
 for(trial=0;trial<3;trial++){
  clear();p=CreatePen(PS_SOLID,1,RGB(0,0,0));op=SelectObject(dc,p);ob=SelectObject(dc,GetStockObject(NULL_BRUSH));SetROP2(dc,R2_COPYPEN);getCount();
  start=GetTickCount();for(i=0;i<16;i++)Ellipse(dc,7,9,w/2,80);elapsed=GetTickCount()-start;count=getCount();
  line("K_BLACK_MS",elapsed);line("K_BLACK_CALLS",16);line("K_BLACK_ADMIT",count);SelectObject(dc,op);SelectObject(dc,ob);DeleteObject(p);
  clear();p=CreatePen(PS_SOLID,1,RGB(0,255,0));op=SelectObject(dc,p);ob=SelectObject(dc,GetStockObject(NULL_BRUSH));SetROP2(dc,R2_XORPEN);dump("kernel_xor_before");getCount();
  start=GetTickCount();for(i=0;i<16;i++)Ellipse(dc,7,9,w/2,80);elapsed=GetTickCount()-start;count=getCount();
  line("K_GREEN_MS",elapsed);line("K_GREEN_CALLS",16);line("K_GREEN_ADMIT",count);dump("kernel_xor_after");SelectObject(dc,op);SelectObject(dc,ob);DeleteObject(p);
 }
}


static COLORREF canonical[16]={RGB(0,0,0),RGB(0,0,128),RGB(0,128,0),RGB(0,128,128),RGB(128,0,0),RGB(128,0,128),RGB(128,128,0),RGB(192,192,192),RGB(128,128,128),RGB(0,0,255),RGB(0,255,0),RGB(0,255,255),RGB(255,0,0),RGB(255,0,255),RGB(255,255,0),RGB(255,255,255)};
static void extensions(void){int i,pw,k;HPEN p,op;HBRUSH b,ob;LOGPEN before,after;char label[40];WORD n;
 for(pw=0;pw<2;pw++)for(i=0;i<16;i++){
  clear();p=CreatePen(PS_SOLID,pw,canonical[i]);op=SelectObject(dc,p);ob=SelectObject(dc,GetStockObject(NULL_BRUSH));GetObject(p,sizeof(before),(LPSTR)&before);getCount();
  line("EXT_ELLIPSE_RETURN",Ellipse(dc,7,9,w/2,80));n=getCount();GetObject(p,sizeof(after),(LPSTR)&after);
  line("EXT_PEN_PRESERVED",!_fmemcmp((LPSTR)&before,(LPSTR)&after,sizeof(before)));line("EXT_COLOR",i);line("EXT_WIDTH",pw);line("EXT_NATIVE",n);
  wsprintf(label,"copy_w%d_c%d",pw,i);dump(label);SelectObject(dc,op);SelectObject(dc,ob);DeleteObject(p);
 }
 for(k=0;k<4;k++){
  clear();p=CreatePen(k==3?PS_DASH:PS_SOLID,1,RGB(255,0,0));b=k==2?GetStockObject(GRAY_BRUSH):GetStockObject(NULL_BRUSH);op=SelectObject(dc,p);ob=SelectObject(dc,b);getCount();
  if(k==0)Ellipse(dc,7,9,9,11);else if(k==1)Ellipse(dc,-400,-200,w+400,h+200);else Ellipse(dc,7,9,w/2,80);
  line("REJECT_KIND",k);line("REJECT_NATIVE",getCount());wsprintf(label,"reject_%d",k);dump(label);SelectObject(dc,op);SelectObject(dc,ob);DeleteObject(p);
 }
}

int PASCAL WinMain(HINSTANCE inst,HINSTANCE prev,LPSTR cmd,int show){int i,j,c,hidden=0,shown=0;HPEN pen,op;HBRUSH ob,b;RECT r;HDC mem;HBITMAP bm,oldbm;HINSTANCE cube;DWORD t;
 logf=_lcreat("C:\\PROBE.LOG",0);dc=GetDC(NULL);w=GetSystemMetrics(SM_CXSCREEN);h=GetSystemMetrics(SM_CYSCREEN);profile=w==640?2:(w==320?1:3);
 getCount=(COUNTERPROC)GetProcAddress(GetModuleHandle("DISPLAY"),(LPSTR)504L);line("COUNTER_FOUND",getCount!=NULL);if(!getCount){_lclose(logf);return 2;}getCount();
 line("REAL_MODE",!(GetWinFlags()&WF_PMODE));line("WIDTH",w);line("HEIGHT",h);line("COLORS",GetDeviceCaps(dc,NUMCOLORS));line("CURVECAPS",GetDeviceCaps(dc,CURVECAPS));line("PROFILE",profile);
 do{c=ShowCursor(FALSE);hidden++;}while(c>=0&&hidden<40);SetCursor(NULL);
 clear();for(i=0;i<8;i++){r.left=i*w/8;r.right=(i+1)*w/8;r.top=0;r.bottom=h;b=CreateSolidBrush(colors[i]);FillRect(dc,&r,b);DeleteObject(b);}dump("color_chart");
 ell(0,0,0,R2_COPYPEN,0);dump("pen0_color");ell(0,1,0,R2_COPYPEN,0);dump("pen1_color");
 ell(0,0,1,R2_COPYPEN,0);dump("solid_color");ell(0,1,1,R2_XORPEN,0);dump("xor_color");
 clear();dump("erase_before");pen=CreatePen(PS_SOLID,1,RGB(0,255,0));op=SelectObject(dc,pen);ob=SelectObject(dc,GetStockObject(NULL_BRUSH));SetROP2(dc,R2_XORPEN);Ellipse(dc,7,9,w-6,h-8);dump("xor_once");Ellipse(dc,7,9,w-6,h-8);dump("erase_after");SelectObject(dc,op);SelectObject(dc,ob);DeleteObject(pen);
 ell(1,0,0,R2_COPYPEN,1);dump("clipped_fullwidth");ell(1,1,1,R2_COPYPEN,0);dump("offscreen_solid");ell(2,1,0,R2_COPYPEN,0);dump("tiny_fallback");
 clear();SetCursor(LoadCursor(NULL,IDC_ARROW));do{c=ShowCursor(TRUE);shown++;}while(c<0&&shown<80);SetCursorPos(20,20);pump(60);dump("cursor_before");
 pen=CreatePen(PS_SOLID,0,RGB(255,0,0));op=SelectObject(dc,pen);ob=SelectObject(dc,GetStockObject(GRAY_BRUSH));Ellipse(dc,5,6,65,54);dump("cursor_overlap");SetCursorPos(w-1,h-1);pump(60);dump("cursor_moved");while(shown-->0)ShowCursor(FALSE);SetCursor(NULL);dump("cursor_hidden");SelectObject(dc,op);SelectObject(dc,ob);DeleteObject(pen);
 clear();mem=CreateCompatibleDC(dc);bm=CreateCompatibleBitmap(dc,w,h);oldbm=SelectObject(mem,bm);PatBlt(mem,0,0,w,h,WHITENESS);pen=CreatePen(PS_SOLID,1,RGB(0,0,255));op=SelectObject(mem,pen);ob=SelectObject(mem,GetStockObject(GRAY_BRUSH));Ellipse(mem,3,4,w-4,h-5);line("MEMORY_BLIT",BitBlt(dc,0,0,w,h,mem,0,0,SRCCOPY));dump("memory_ellipse_blit");SelectObject(mem,op);SelectObject(mem,ob);DeleteObject(pen);SelectObject(mem,oldbm);DeleteObject(bm);DeleteDC(mem);
 kernels();extensions();line("ELLIPSE_DONE",1);flush();ReleaseDC(NULL,dc);while(hidden-->0)ShowCursor(TRUE);
 cube=WinExec("C:\\WINXT\\CUBE.EXE /Q",SW_SHOWNORMAL);line("CUBE_EXEC",cube);flush();t=GetTickCount();
 while(GetModuleHandle("CUBE")&&GetTickCount()-t<300000UL)pump(55);
 line("CUBE_RETURNED",!GetModuleHandle("CUBE"));line("COMPLETE",1);_lclose(logf);return 0;
}
