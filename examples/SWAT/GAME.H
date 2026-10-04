/* Original integer-only fly swatter rules. Shared by native and host tests. */
#define NFLY 3
#define FW 148
#define FH 174
typedef struct { int x,y,dx,dy,ttl,wait,active; } FLY;
static FLY flies[NFLY];
static unsigned short seed=621;
static unsigned score;
static int hearts,playing,paused,phase,markx,marky,marklife;
static unsigned ticks;
static unsigned rnd(void){seed=(unsigned short)((unsigned long)seed*25173UL+13849UL);return seed;}
static void spawn(int i){FLY *f=&flies[i];f->x=14+(rnd()%119);f->y=43+(rnd()%83);f->dx=(rnd()&16)?2:-2;f->dy=(rnd()&16)?1:-1;f->ttl=90-(score/100>30?30:score/100);f->active=1;f->wait=0;}
static void newgame(void){int i;score=0;hearts=3;paused=0;playing=1;phase=0;marklife=0;ticks=0;seed=621;for(i=0;i<NFLY;i++){flies[i].active=0;flies[i].wait=-1;}spawn(0);}
static void lose(void){if(hearts>0)--hearts;if(!hearts){playing=0;paused=0;}}
static int swat(int x,int y){int i;if(!playing||paused)return -2;markx=x;marky=y;marklife=2;for(i=NFLY-1;i>=0;i--)if(flies[i].active&&x>=flies[i].x-8&&x<=flies[i].x+8&&y>=flies[i].y-8&&y<=flies[i].y+8){flies[i].active=0;flies[i].wait=4;score=score>59980U?59990U:score+10;return i;}lose();return -1;}
static void stepgame(void){int i,speed;FLY *f;if(!playing||paused)return;ticks++;phase^=1;if(marklife)marklife--;speed=score>=200?3:2;
 for(i=0;i<NFLY&&playing;i++){f=&flies[i];if(!f->active){if(f->wait>0)--f->wait;if(!f->wait)spawn(i);continue;}
 if((ticks+i*3)%9==0){f->dx=(rnd()&16)?speed:-speed;f->dy=(rnd()&32)?1:-1;}
 f->x+=f->dx;f->y+=f->dy;if(f->x<13){f->x=13;f->dx=speed;}if(f->x>135){f->x=135;f->dx=-speed;}
 if(f->y<39){f->y=39;f->dy=1;}if(f->y>135){f->y=135;f->dy=-1;}
 if(--f->ttl<=0){f->active=0;f->wait=8;lose();}
 }}
