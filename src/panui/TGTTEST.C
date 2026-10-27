#include <assert.h>
#include "PANTGT.H"
int main(void)
{
 PANTARGET p;int i;int commands[7]={PK_RIGHT,PK_RIGHT,PK_RIGHT,PK_HOME,PK_DOWN,PK_DOWN,PK_RIGHT};
 PanTargetInit(&p,0,0,160,100,40,25,8,1);
 for(i=0;i<7;i++)assert(PanTargetCommand(&p,commands[i],0,0));
 assert(p.x==40 && p.y==50 && p.home && p.moved);
 PanTargetInit(&p,0,0,160,100,40,25,8,1);
 for(i=0;i<12;i++)PanTargetCommand(&p,PK_RIGHT,0,0);
 PanTargetCommand(&p,PK_LEFT,0,0);assert(p.x==120);
 PanTargetCommand(&p,PK_END,156,79);assert(p.x==160 && p.y==79);
 PanTargetCommand(&p,PK_END,-50,300);assert(p.x==0 && p.y==100);
 PanTargetInit(&p,0,0,0,200,50,50,1,1);
 PanTargetCommand(&p,PK_DOWN,0,0);assert(p.y==50);
 PanTargetCommand(&p,PK_END,0,37);assert(p.y==37);
 assert(!PanTargetCommand(&p,PK_SETTINGS,0,0) && p.y==37);
 PanTargetInit(&p,0,0,320,56,8,4,8,4);
 PanTargetCommand(&p,PK_END,315,53);assert(p.x==320 && p.y==56);
 PanTargetCommand(&p,PK_HOME,0,0);assert(!p.x && !p.y);
 PanTargetInit(&p,10,15,1728,1848,50,50,1,1);
 PanTargetCommand(&p,PK_HOME,0,0);PanTargetCommand(&p,PK_RIGHT,0,0);
 assert(p.home && p.x==50 && p.y==0);
 return 0;
}
