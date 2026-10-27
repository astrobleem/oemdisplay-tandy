#include "PANTGT.H"
static int Bound(long value,int limit,int align)
{
 if(value<0)value=0;
 if(value>limit)value=limit;
 return (int)(value/align)*align;
}
void PanTargetInit(PANTARGET *p,int x,int y,int mx,int my,int sx,int sy,int ax,int ay)
{
 p->x=x;p->y=y;p->maxX=mx;p->maxY=my;p->stepX=sx;p->stepY=sy;
 p->alignX=ax;p->alignY=ay;p->moved=p->home=0;
}
int PanTargetCommand(PANTARGET *p,int command,int endX,int endY)
{
 long x=p->x,y=p->y;
 switch(command){
 case PK_HOME:x=y=0;p->home=1;break;
 case PK_END:
  x=endX;y=endY;
  if(x>0)x=((x+p->alignX-1)/p->alignX)*p->alignX;
  if(y>0)y=((y+p->alignY-1)/p->alignY)*p->alignY;
  break;
 case PK_LEFT:x-=p->stepX;break;case PK_RIGHT:x+=p->stepX;break;
 case PK_UP:y-=p->stepY;break;case PK_DOWN:y+=p->stepY;break;
 default:return 0;
 }
 p->x=Bound(x,p->maxX,p->alignX);p->y=Bound(y,p->maxY,p->alignY);
 p->moved=1;return 1;
}
