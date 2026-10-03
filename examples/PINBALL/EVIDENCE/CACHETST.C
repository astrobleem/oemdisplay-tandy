/* Host-only stub regression for rendering control flow.
   PINBALL.C SHA256: 0d3bab6870eca0bc011bc9887865b9fb206228307ee52756de57c0a522afb644
   Not a GDI, Win16 or pixel-accuracy emulator. */

#include <stdio.h>
#include <assert.h>
#include <string.h>
typedef int HDC;
typedef int HBITMAP;
typedef int HWND;
typedef struct { int left,top,right,bottom; } RECT;
#define Q 64
#define SYSTEM_FIXED_FONT 10
#define WHITE_PEN 11
#define BLACK_BRUSH 12
#define TRANSPARENT 1
#define BLACKNESS 0
#define WHITENESS 1
#define SRCCOPY 2
#define RGB(r,g,b) 0
#define lstrlen strlen
#define lstrcpy strcpy
#define lstrcat strcat
static int bx=72*Q,by=115*Q,balls=3,la,ra,live;
static long score;
static int bumpx[3]={42,102,72},bumpy[3]={37,37,65};
static int faildc,failbm,failsel,failcopy,failfill,ndc,nbm,del_dc,del_bm,screenfill,copies,invalidcopy;
static int selected=1;
static void MoveTo(HDC d,int x,int y){}
static void LineTo(HDC d,int x,int y){}
static void TextOut(HDC d,int x,int y,char*s,int len){}
static int GetStockObject(int n){return n;}
static void SetBkMode(HDC d,int n){}
static void SetTextColor(HDC d,int n){}
static void SetBkColor(HDC d,int n){}
static void Ellipse(HDC d,int x,int y,int a,int b){}
static int SelectObject(HDC d,int o){int old=selected;if(o!=1&&o!=200)return 99;if(failsel&&o==200)return 0;selected=o;return old;}
static int DeleteDC(HDC d){++del_dc;selected=0;return 1;}
static int DeleteObject(int o){++del_bm;return 1;}
static void GetClientRect(HWND w,RECT*r){r->left=r->top=0;r->right=154;r->bottom=181;}
static HDC CreateCompatibleDC(HDC d){++ndc;selected=1;return faildc?0:100;}
static HBITMAP CreateCompatibleBitmap(HDC d,int w,int h){++nbm;return failbm?0:200;}
static int PatBlt(HDC d,int x,int y,int w,int h,int rop){if(d==2&&rop==BLACKNESS)++screenfill;return !(d==100&&failfill);}
static int BitBlt(HDC d,int x,int y,int w,int h,HDC b,int a,int c,int rop){++copies;if(selected!=200)++invalidcopy;return !(failcopy||selected!=200);}
static int ox,oy=17,paused,lmask,rmask;
static HDC board;
static HBITMAP boardbits,oldbits;
static void line(HDC d,int x,int y,int xx,int yy){MoveTo(d,ox+x,oy+y);LineTo(d,ox+xx,oy+yy);}
static void text(HDC d,int x,int y,char *s){TextOut(d,x,y,s,lstrlen(s));}
static void number(char *s,long n){char t[12];int i=0,j=0;do{t[i++]=(char)('0'+n%10);n/=10;}while(n);while(i)s[j++]=t[--i];s[j]=0;}
static void setup(HDC d){
 SelectObject(d,GetStockObject(SYSTEM_FIXED_FONT));SetBkMode(d,TRANSPARENT);
 SetTextColor(d,RGB(255,255,255));SetBkColor(d,RGB(0,0,0));
 SelectObject(d,GetStockObject(WHITE_PEN));SelectObject(d,GetStockObject(BLACK_BRUSH));
}
static void table(HDC d){int i;
 setup(d);line(d,5,132,5,5);line(d,5,5,139,5);line(d,139,5,139,132);
 line(d,5,85,33,113);line(d,139,85,111,113);
 for(i=0;i<3;++i){Ellipse(d,ox+bumpx[i]-8,oy+bumpy[i]-8,ox+bumpx[i]+9,oy+bumpy[i]+9);Ellipse(d,ox+bumpx[i]-3,oy+bumpy[i]-3,ox+bumpx[i]+4,oy+bumpy[i]+4);}
 text(d,ox,oy+138,"Z / flip Space go");
}
static void freeboard(void){if(board){SelectObject(board,oldbits);DeleteDC(board);DeleteObject(boardbits);board=NULL;boardbits=NULL;}}
static void cache(HWND w,HDC d){RECT r;
 if(board)return;GetClientRect(w,&r);board=CreateCompatibleDC(d);if(!board)return;
 boardbits=CreateCompatibleBitmap(d,r.right,r.bottom);
 if(!boardbits){DeleteDC(board);board=NULL;return;}
 oldbits=SelectObject(board,boardbits);
 if(!oldbits){DeleteDC(board);DeleteObject(boardbits);board=NULL;boardbits=NULL;return;}
 if(!PatBlt(board,0,0,r.right,r.bottom,BLACKNESS)){freeboard();return;}
 table(board);
}
static void paint(HWND w,HDC d,RECT *r){char s[32],n[12];
 cache(w,d);
 if(!board||!BitBlt(d,r->left,r->top,r->right-r->left,r->bottom-r->top,board,r->left,r->top,SRCCOPY)){PatBlt(d,r->left,r->top,r->right-r->left,r->bottom-r->top,BLACKNESS);table(d);}
 setup(d);
 if(r->top<17){number(n,score);lstrcpy(s,"S:");lstrcat(s,n);text(d,ox+1,1,s);
  number(n,(long)balls);lstrcpy(s,"B:");lstrcat(s,n);text(d,ox+112,1,s);}
 if(r->bottom>oy+98&&r->top<oy+127){
  line(d,33,113,63,121-la*4);line(d,33,114,63,122-la*4);
  line(d,111,113,81,121-ra*4);line(d,111,114,81,122-ra*4);}
 /* Tiny square ball: two-dimensional GDI primitive, no ellipse scan conversion. */
 PatBlt(d,ox+bx/Q-2,oy+by/Q-2,5,5,WHITENESS);
 if(!live&&r->bottom>oy+90&&r->top<oy+105)text(d,ox+16,oy+90,balls?"SPACE launch":"SPACE new game");
 if(paused&&r->bottom>oy+80&&r->top<oy+95)text(d,ox+32,oy+80,"P: resume");
}

static void clear(void){board=boardbits=oldbits=0;faildc=failbm=failsel=failcopy=failfill=ndc=nbm=del_dc=del_bm=screenfill=copies=invalidcopy=0;selected=1;}
int main(void){RECT r={0,0,154,181};
clear();faildc=1;paint(1,2,&r);assert(!board && screenfill==1 && !nbm);printf("DC failure: board=%d screen_background_fills=%d\n",board,screenfill);
clear();failbm=1;paint(1,2,&r);assert(!board && del_dc==1 && screenfill==1 && !del_bm);printf("bitmap failure: board=%d deleted_dc=%d screen_background_fills=%d\n",board,del_dc,screenfill);
clear();failsel=1;paint(1,2,&r);assert(!board && !boardbits && !copies && screenfill==1 && del_dc==1 && del_bm==1);printf("select failure: board=%d oldbits=%d attempted_invalid_copy=%d screen_background_fills=%d\n",board,oldbits,invalidcopy,screenfill);freeboard();
clear();failcopy=1;paint(1,2,&r);assert(board && copies==1 && screenfill==1);printf("copy failure: board=%d copy_calls=%d screen_background_fills=%d\n",board,copies,screenfill);freeboard();
clear();failfill=1;paint(1,2,&r);assert(!board && !boardbits && !copies && screenfill==1 && del_dc==1 && del_bm==1);printf("cache clear failure: board=%d copy_calls=%d screen_background_fills=%d\n",board,copies,screenfill);freeboard();
clear();paint(1,2,&r);paint(1,2,&r);freeboard();freeboard();assert(ndc==1 && nbm==1 && del_dc==1 && del_bm==1 && !board && !boardbits);printf("normal lifecycle: dc_allocations=%d bitmap_allocations=%d dc_deletes=%d bitmap_deletes=%d board_after_free=%d\n",ndc,nbm,del_dc,del_bm,board);
puts("PASS: all six stub control-flow cases");return 0;}
