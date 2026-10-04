#include <assert.h>
#include <stdio.h>
#include "GAME.H"
int main(void){int i,j,r,x,y,life;unsigned s;newgame();assert(hearts==3&&playing&&!paused&&score==0);x=flies[0].x;y=flies[0].y;r=swat(x,y);assert(r>=0&&score==10&&hearts==3);paused=1;x=flies[1].x;y=flies[1].y;stepgame();assert(flies[1].x==x&&flies[1].y==y);assert(swat(x,y)==-2);paused=0;for(i=0;i<3;i++)swat(5,33);assert(!playing&&hearts==0);assert(swat(5,33)==-2);newgame();score=59990;swat(flies[0].x,flies[0].y);assert(score==59990);newgame();for(i=0;i<3;i++){flies[i].active=1;flies[i].ttl=1;}stepgame();assert(hearts==0&&!playing);
 for(r=0;r<1000;r++){newgame();seed=(unsigned short)(r+1);for(j=0;j<2000;j++){if(!playing)newgame();if(j%17==0)paused=!paused;life=hearts;s=score;stepgame();assert(hearts>=0&&hearts<=3&&score<=59990);if(paused)assert(hearts==life&&score==s);for(i=0;i<3;i++)if(flies[i].active){assert(flies[i].x>=13&&flies[i].x<=135);assert(flies[i].y>=39&&flies[i].y<=135);assert(flies[i].ttl>0);}if(j%5==0)swat(flies[j%3].x,flies[j%3].y);}}
 puts("PASS rules, hit/miss, pause, exhaustion, cap, restart, and 2,000,000 sampled ticks");return 0;}
