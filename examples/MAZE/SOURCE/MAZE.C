/* MAZE: integer-only, bounded 32-ray Windows 3.0 demonstration. */
#define WINVER 0x0300
#ifndef MAZE_HOST
#include <windows.h>
#endif
#define RAYS 32
#define MAPSIZE 12
static const char world[MAPSIZE][MAPSIZE+1]={
 "############",
 "#..........#",
 "#.##.###.#.#",
 "#.#......#.#",
 "#.#.####.#.#",
 "#...#..#...#",
 "#.#.#..#.#.#",
 "#.#.####.#.#",
 "#.#......#.#",
 "#.###.##.#.#",
 "#..........#",
 "############"};
static const int sine[256]={0,6,13,19,25,31,38,44,50,56,62,68,74,80,86,92,98,104,109,115,121,126,132,137,142,147,152,157,162,167,172,177,181,185,190,194,198,202,206,209,213,216,220,223,226,229,231,234,237,239,241,243,245,247,248,250,251,252,253,254,255,255,256,256,256,256,256,255,255,254,253,252,251,250,248,247,245,243,241,239,237,234,231,229,226,223,220,216,213,209,206,202,198,194,190,185,181,177,172,167,162,157,152,147,142,137,132,126,121,115,109,104,98,92,86,80,74,68,62,56,50,44,38,31,25,19,13,6,0,-6,-13,-19,-25,-31,-38,-44,-50,-56,-62,-68,-74,-80,-86,-92,-98,-104,-109,-115,-121,-126,-132,-137,-142,-147,-152,-157,-162,-167,-172,-177,-181,-185,-190,-194,-198,-202,-206,-209,-213,-216,-220,-223,-226,-229,-231,-234,-237,-239,-241,-243,-245,-247,-248,-250,-251,-252,-253,-254,-255,-255,-256,-256,-256,-256,-256,-255,-255,-254,-253,-252,-251,-250,-248,-247,-245,-243,-241,-239,-237,-234,-231,-229,-226,-223,-220,-216,-213,-209,-206,-202,-198,-194,-190,-185,-181,-177,-172,-167,-162,-157,-152,-147,-142,-137,-132,-126,-121,-115,-109,-104,-98,-92,-86,-80,-74,-68,-62,-56,-50,-44,-38,-31,-25,-19,-13,-6};
static int px=384,py=384,angle=0,leg=0,turning=0;
static unsigned walls[RAYS];
static unsigned char shades[RAYS];
static unsigned long frames,paints;
static int solid(int x,int y){return x<0||y<0||x>=MAPSIZE*256||y>=MAPSIZE*256||world[y>>8][x>>8]!='.';}
static int walkable(int x,int y){return !solid(x-48,y-48)&&!solid(x+48,y-48)&&!solid(x-48,y+48)&&!solid(x+48,y+48);}
static void advance(void){
 static const int tx[4]={2688,2688,384,384},ty[4]={384,2688,2688,384};
 int nx,ny;
 if(turning){angle=(angle+4)&255;if(angle==((leg*64)&255))turning=0;return;}
 nx=px+sine[(angle+64)&255]*24/256;ny=py+sine[angle]*24/256;
 if((angle==0&&nx>=tx[leg])||(angle==64&&ny>=ty[leg])||(angle==128&&nx<=tx[leg])||(angle==192&&ny<=ty[leg])){
  px=tx[leg];py=ty[leg];leg=(leg+1)&3;turning=1;return;
 }
 if(walkable(nx,ny)){px=nx;py=ny;}else{leg=(leg+1)&3;turning=1;}
}
static void cast(int height){
 int i,a,dx,dy,sx,sy,mx,my,n,side,off,h;
 unsigned long xx,yy,dist,perp;
 unsigned ax,ay,ex,ey;
 if(height<0)height=0;if(height>4096)height=4096;
 for(i=0;i<RAYS;i++){
  off=(i*46/31)-23;a=(angle+off+256)&255;
  dx=sine[(a+64)&255];dy=sine[a];ax=dx<0?-dx:dx;ay=dy<0?-dy:dy;
  mx=px>>8;my=py>>8;sx=dx<0?-1:1;sy=dy<0?-1:1;
  ex=dx<0?(px&255):256-(px&255);ey=dy<0?(py&255):256-(py&255);
  xx=dx==0?0x3fffffffUL:(unsigned long)ex*ay;
  yy=dy==0?0x3fffffffUL:(unsigned long)ey*ax;
  dist=256;side=0;
  for(n=0;n<24;n++){
   if(xx<yy||(xx==yy&&(mx+sx<0||mx+sx>=MAPSIZE||world[my][mx+sx]!='.'))){dist=ex;ex+=256;xx+=(unsigned long)ay*256UL;mx+=sx;side=0;}else{dist=ey;ey+=256;yy+=(unsigned long)ax*256UL;my+=sy;side=1;}
   if(mx<0||my<0||mx>=MAPSIZE||my>=MAPSIZE||world[my][mx]!='.')break;
  }
  perp=dist*(unsigned)sine[(off+320)&255]/(side?ay:ax);
  if(perp<32)perp=32;
  h=(int)((unsigned long)height*160UL/perp);if(h>height)h=height;if(h<1&&height)h=1;
  walls[i]=(unsigned)h;shades[i]=(unsigned char)(side+(perp>768?2:0));
 }
}
#ifndef MAZE_HOST
static HINSTANCE instance;
static HBRUSH brushes[4];
static HDC memoryDC;
static HBITMAP canvas,previousBitmap;
static int canvasW,canvasH,bufferFailed;
static int paused,measuring,failedTimer,capturing;
static DWORD started,freeStart,freeWarm,setupMs;
static char logpath[144];
static void output(char *text){HFILE f=_lopen(logpath,OF_WRITE);if(f==HFILE_ERROR)f=_lcreat(logpath,0);if(f!=HFILE_ERROR){_llseek(f,0L,2);_lwrite(f,text,lstrlen(text));_lclose(f);}}
static void dumpframe(void){HFILE f=_lcreat("C:\\MAZE.RAW",0);if(f!=HFILE_ERROR){_lwrite(f,(LPSTR)0xb8000000L,32768U);_lclose(f);}}
static void finish(HWND w){char b[220];DWORD elapsed=GetTickCount()-started;wsprintf(b,"elapsed_ms=%lu setup_ms=%lu frames=%lu paints=%lu free_start=%lu free_end=%lu free_warm=%lu timer_failed=%d buffer_failed=%d\r\n",elapsed,setupMs,frames,paints,freeStart,GetFreeSpace(0),freeWarm,failedTimer,bufferFailed);output(b);DestroyWindow(w);}
static void releaseCanvas(void){if(memoryDC){if(canvas){SelectObject(memoryDC,previousBitmap);DeleteObject(canvas);}DeleteDC(memoryDC);}memoryDC=NULL;canvas=NULL;canvasW=canvasH=0;}
static int ensureCanvas(HDC dc,int width,int height){
 if(memoryDC&&canvasW==width&&canvasH==height)return 1;releaseCanvas();if(width<1||height<1||width>640||height>200)return 0;
 memoryDC=CreateCompatibleDC(dc);if(!memoryDC){bufferFailed=1;return 0;}canvas=CreateCompatibleBitmap(dc,width,height);
 if(!canvas){releaseCanvas();bufferFailed=1;return 0;}previousBitmap=SelectObject(memoryDC,canvas);canvasW=width;canvasH=height;return 1;
}
static void draw(HDC dc,RECT *r){
 int i,j,x,x2,top,bottom,height=r->bottom,width=r->right;RECT z;
 if(width<=0||height<=0)return;
 /* Group adjacent identical wall spans. No per-frame GDI objects or bitmap. */
 for(i=0;i<RAYS;i=j){
  j=i+1;while(j<RAYS&&walls[j]==walls[i]&&shades[j]==shades[i])j++;
  x=(int)((long)i*width/RAYS);x2=(int)((long)j*width/RAYS);
  if(x2<=x)continue;top=(height-(int)walls[i])/2;bottom=top+walls[i];
  SetRect(&z,x,0,x2,top);FillRect(dc,&z,GetStockObject(BLACK_BRUSH));
  SetRect(&z,x,top,x2,bottom);FillRect(dc,&z,brushes[shades[i]]);
  SetRect(&z,x,bottom,x2,height);FillRect(dc,&z,GetStockObject(DKGRAY_BRUSH));
 }
}
LONG FAR PASCAL WndProc(HWND w,UINT m,WPARAM wp,LPARAM lp){
 RECT r;PAINTSTRUCT ps;HDC dc;
 switch(m){
 case WM_CREATE:
  brushes[0]=GetStockObject(WHITE_BRUSH);brushes[1]=GetStockObject(LTGRAY_BRUSH);brushes[2]=GetStockObject(GRAY_BRUSH);brushes[3]=GetStockObject(DKGRAY_BRUSH);
  started=GetTickCount();freeStart=GetFreeSpace(0);if(measuring)output("CREATE\r\n");if(!SetTimer(w,1,125,NULL)){failedTimer=1;SetWindowText(w,"Maze: timer failed");}return 0;
 case WM_SIZE:GetClientRect(w,&r);cast(r.bottom);InvalidateRect(w,NULL,FALSE);return 0;
 case WM_ERASEBKGND:return 1;
 case WM_TIMER:
  if(wp!=1)return 0;if(measuring&&!frames)output("TIMER\r\n");if(capturing && frames==30){dumpframe();output("CAPTURED\r\n");finish(w);return 0;}if(measuring&&!capturing&&GetTickCount()-started>=10000UL){finish(w);return 0;}
  if(paused||IsIconic(w))return 0;advance();GetClientRect(w,&r);cast(r.bottom);frames++;if(frames==5)freeWarm=GetFreeSpace(0);InvalidateRect(w,NULL,FALSE);return 0;
 case WM_PAINT:dc=BeginPaint(w,&ps);GetClientRect(w,&r);if(ensureCanvas(dc,r.right,r.bottom)){draw(memoryDC,&r);BitBlt(dc,0,0,r.right,r.bottom,memoryDC,0,0,SRCCOPY);}else draw(dc,&r);paints++;EndPaint(w,&ps);if(paints==1){setupMs=GetTickCount()-started;started=GetTickCount();}return 0;
 case WM_KEYDOWN:if(wp==VK_ESCAPE){DestroyWindow(w);return 0;}if(wp==VK_SPACE){paused=!paused;SetWindowText(w,paused?"Maze paused":"Maze");return 0;}break;
 case WM_DESTROY:releaseCanvas();KillTimer(w,1);PostQuitMessage(0);return 0;
 }return DefWindowProc(w,m,wp,lp);
}
int PASCAL WinMain(HINSTANCE inst,HINSTANCE prev,LPSTR cmd,int show){
 WNDCLASS wc;HWND w;MSG msg;int i,n,width,height;
 instance=inst;capturing=(cmd[0]=='/'&&(cmd[1]=='c'||cmd[1]=='C'));measuring=capturing||(cmd[0]=='/'&&(cmd[1]=='t'||cmd[1]=='T'));
 GetModuleFileName(inst,logpath,sizeof(logpath));n=lstrlen(logpath);for(i=n-1;i>=0&&logpath[i]!='\\'&&logpath[i]!=':';i--);logpath[i+1]=0;lstrcat(logpath,"MAZE.LOG");
 if(measuring){HFILE f=_lcreat(logpath,0);if(f!=HFILE_ERROR)_lclose(f);}
 if(!prev){wc.style=CS_HREDRAW|CS_VREDRAW;wc.lpfnWndProc=WndProc;wc.cbClsExtra=0;wc.cbWndExtra=0;wc.hInstance=inst;wc.hIcon=NULL;wc.hCursor=LoadCursor(NULL,IDC_ARROW);wc.hbrBackground=NULL;wc.lpszMenuName=NULL;wc.lpszClassName="TandyMaze";if(!RegisterClass(&wc))return 1;}
 width=GetSystemMetrics(SM_CXSCREEN);if(width>300)width=300;height=GetSystemMetrics(SM_CYSCREEN)-16;if(height>184)height=184;
 w=CreateWindow("TandyMaze","Maze",WS_OVERLAPPEDWINDOW,0,0,width,height,NULL,NULL,inst,NULL);if(!w)return 2;ShowWindow(w,show);UpdateWindow(w);
 while(GetMessage(&msg,NULL,0,0)){TranslateMessage(&msg);DispatchMessage(&msg);}return msg.wParam;
}
#endif
