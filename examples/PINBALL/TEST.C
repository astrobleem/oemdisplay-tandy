/* The same tests compile on the host and under Microsoft C 6 /G0 /Gw. */
#ifdef HOSTMAIN
#include <stdio.h>
#else
#define WINVER 0x0300
#include <windows.h>
#endif
#include "PHYSICS.H"
#define CHECK(x) do{if(!(x))return __LINE__;}while(0)
static int tests(void){int i,j,miny;unsigned seed=7;long stamp;
 reset();CHECK(balls==3&&!live);launch();miny=by;
 for(i=0;i<500&&live;i++){step();if(by<miny)miny=by;}
 CHECK(miny<60*Q);CHECK(!live&&balls==2);CHECK(score>0);
 reset();live=1;bx=72*Q;by=135*Q;vy=112;step();CHECK(balls==2&&!live&&drains==1);
 reset();live=1;bx=42*Q;by=26*Q;vy=50;step();CHECK(score==10&&vy<0);
 for(i=0;i<2000&&live&&by<40*Q;i++)step();
 CHECK(by>=40*Q||!live);
 reset();live=1;bx=50*Q;by=110*Q;vy=30;leftkey=1;step();CHECK(flips>0&&vy<0);
 leftkey=0;for(i=0;i<5;i++)step();CHECK(la==0);
 reset();live=1;bx=94*Q;by=110*Q;vy=30;rightkey=1;step();CHECK(flips>0&&vy<0);
 rightkey=0;for(i=0;i<5;i++)step();CHECK(ra==0);
 reset();live=1;bx=8*Q;by=20*Q;vx=-112;step();CHECK(vx>0&&bx>=8*Q);
 reset();for(i=0;i<3;i++){launch();bx=72*Q;by=135*Q;vy=112;step();}CHECK(!balls&&!live);launch();CHECK(!live);
 reset();score=999990L;live=1;bx=42*Q;by=26*Q;vy=50;step();CHECK(score==999990L);
 /* Replaying an identical input schedule must reproduce its result. */
 stamp=0;for(j=0;j<2;j++){reset();launch();for(i=0;i<1000;i++){
  leftkey=(i/9)%2;rightkey=(i/13)%2;if(!live&&balls)launch();step();}
  if(j)CHECK(stamp==score+bx+by);else stamp=score+bx+by;
 }
#ifdef HOSTMAIN
 for(j=0;j<100;j++)
#else
 for(j=0;j<1;j++)
#endif
 {reset();launch();for(i=0;i<20000;i++){
  seed=(unsigned)((long)seed*109+89)&32767;leftkey=seed&1;rightkey=(seed>>4)&1;
  if(!live){if(!balls)reset();launch();}step();
  CHECK(bx>=8*Q&&bx<=136*Q);CHECK(by>=0&&by<=136*Q);
  CHECK(vx>=-112&&vx<=112&&vy>=-112&&vy<=112);CHECK(score>=0&&score<=999990L);
 }}return 0;
}
#ifdef HOSTMAIN
int main(void){int r=tests();printf("%s line=%d: launch, bumper score, both flipper kicks/return, walls, three drains, score limit, replay, 2000000 stress ticks\n",r?"FAIL":"PASS",r);return r?1:0;}
#else
LONG FAR PASCAL WndProc(HWND w,UINT m,WPARAM wp,LPARAM lp){return DefWindowProc(w,m,wp,lp);}
int PASCAL WinMain(HINSTANCE h,HINSTANCE old,LPSTR cmd,int show){int r=tests();HFILE f;char s[160];
 lstrcpy(s,r?"FAIL":"PASS");
 lstrcat(s,": launch, score, left/right, return, walls, drains, limit, replay, 20000 stress ticks\r\nCOMPLETE=1\r\n");
 f=_lcreat("C:\\PINTEST.LOG",0);if(f!=HFILE_ERROR){_lwrite(f,s,lstrlen(s));_lclose(f);}return r;
}
#endif
