#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "JOYCORE.H"
static unsigned checks;
#define CHECK(c) do {checks++;if(!(c)){fprintf(stderr,"FAIL line %d: %s\n",__LINE__,#c);exit(1);}}while(0)
static void burst(unsigned char *r,unsigned *t,unsigned b){unsigned i,a;for(i=0;i<512;i++){r[i]=(unsigned char)((~b&15)<<4);for(a=0;a<4;a++)if(i<t[a])r[i]|=(unsigned char)(1<<a);}}
int main(void){unsigned char r[512];unsigned t[4],a,i,b;JOY_SAMPLE s;JOY_CAL c;unsigned seed=12345;
 t[0]=0;t[1]=1;t[2]=511;t[3]=512;burst(r,t,0);joy_decode(r,512,&s);CHECK(s.axis[0]==0&&s.axis[1]==1&&s.axis[2]==511&&s.axis[3]==512);CHECK(s.early==1&&s.timed==6&&s.timeout==8&&s.buttons==0);
 for(b=0;b<16;b++){burst(r,t,b);joy_decode(r,512,&s);CHECK(s.buttons==b);}
 memset(r,255,sizeof(r));joy_decode(r,512,&s);CHECK(s.timeout==15&&s.timed==0&&s.early==0);CHECK(s.buttons==0);
 memset(r,0,sizeof(r));joy_decode(r,512,&s);CHECK(s.early==15&&s.timeout==0&&s.timed==0&&s.buttons==15);
 joy_decode(r,0,&s);CHECK(s.timeout==15);joy_decode(r,513,&s);CHECK(s.timeout==15);
 for(i=0;i<10000;i++){for(a=0;a<4;a++){seed=(seed*25173u+13849u)&65535u;t[a]=seed%514;}b=seed&15;burst(r,t,b);joy_decode(r,512,&s);for(a=0;a<4;a++){CHECK(s.axis[a]==(t[a]<512?t[a]:512));CHECK(!!(s.timeout&(1<<a))==(t[a]>=512));}CHECK(s.buttons==b);}
 joy_reset(&c);CHECK(c.seen==0&&c.centered==0);CHECK(joy_normal(&c,0,10)==-1);
 for(a=0;a<4;a++){t[a]=50;}burst(r,t,0);joy_decode(r,512,&s);joy_track(&c,&s);joy_center(&c,&s);CHECK(c.centered==15);CHECK(joy_normal(&c,0,50)==-1);
 for(a=0;a<4;a++){t[a]=10;}burst(r,t,0);joy_decode(r,512,&s);joy_track(&c,&s);
 for(a=0;a<4;a++){t[a]=90;}burst(r,t,0);joy_decode(r,512,&s);joy_track(&c,&s);
 for(a=0;a<4;a++){CHECK(joy_normal(&c,a,10)==0);CHECK(joy_normal(&c,a,30)==25);CHECK(joy_normal(&c,a,50)==50);CHECK(joy_normal(&c,a,70)==75);CHECK(joy_normal(&c,a,90)==100);CHECK(joy_normal(&c,a,511)==100);CHECK(joy_normal(&c,a,512)==-1);}
 CHECK(joy_normal(&c,4,50)==-1);memset(r,255,512);joy_decode(r,512,&s);joy_track(&c,&s);CHECK(c.low[0]==10&&c.high[0]==90);joy_center(&c,&s);CHECK(c.centered==0);CHECK(c.center[0]==0);
 /* First low is latched: a later noisy high does not extend the value. */
 memset(r,255,512);r[20]&=254;joy_decode(r,512,&s);CHECK(s.axis[0]==20&&s.timed==1&&s.timeout==14);
 printf("PASS %u checks: independent synthetic pulse/timeout/button/calibration tests\n",checks);return 0;
}
