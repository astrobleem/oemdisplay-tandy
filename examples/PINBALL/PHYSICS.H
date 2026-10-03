/* Integer-only, shared by the Win16 game and host tests. Q6 positions.
   Four bounded substeps per timer message; never catch up wall-clock stalls. */
#define Q 64
#define BALL 3
static int bx,by,vx,vy,live,leftkey,rightkey,la,ra,balls;
static long score;
static int bumpx[3]={42,102,72},bumpy[3]={37,37,65};
static unsigned hits,flips,drains;
static int limit(int v,int m){return v < -m ? -m : (v>m?m:v);}
static int root(int a){int n=0;while((n+1)*(n+1)<=a)++n;return n;}
static void ready(void){bx=72*Q;by=115*Q;vx=vy=0;live=0;}
static void reset(void){score=0;balls=3;leftkey=rightkey=la=ra=0;hits=flips=drains=0;ready();}
static void launch(void){if(!live&&balls){live=1;vx=-14;vy=-112;}}
static void reflect(int dx,int dy,int n,int kick){
 long dot=(long)vx*dx+(long)vy*dy;int d=dx*dx+dy*dy;
 if(!d)return;
 if(dot<0){vx-=(int)(2L*dot*dx/d);vy-=(int)(2L*dot*dy/d);}
 if(kick){vx+=(int)((long)dx*kick/n);vy+=(int)((long)dy*kick/n);}
 vx=limit(vx,112);vy=limit(vy,112);
}
static int circle(int x,int y,int r){
 int dx=bx/Q-x,dy=by/Q-y,n,d;
 if(dx < -r||dx>r||dy < -r||dy>r)return 0;
 d=dx*dx+dy*dy;if(d>=r*r)return 0;
 if(!d){dx=0;dy=-1;d=1;}n=root(d);if(!n)n=1;
 bx=x*Q+(int)((long)dx*(r+1)*Q/n);
 by=y*Q+(int)((long)dy*(r+1)*Q/n);
 reflect(dx,dy,n,20);
 /* Break exact vertical bumper/ceiling loops deterministically. */
 if(vx>-8&&vx<8)vx=x<=72?12:-12;
 return 1;
}
/* Segment capsule: conservative one-pixel separation, max 1.75 pixel travel.
   All projection products explicitly long for a 16-bit compiler. */
static int segment(int x1,int y1,int x2,int y2,int active,int side){
 int dx=x2-x1,dy=y2-y1,len=dx*dx+dy*dy,x,y,n,dd;
 long t;
 x=bx/Q;y=by/Q;
 if(x<(x1<x2?x1:x2)-5||x>(x1>x2?x1:x2)+5||
    y<(y1<y2?y1:y2)-5||y>(y1>y2?y1:y2)+5)return 0;
 t=(long)(x-x1)*dx+(long)(y-y1)*dy;
 if(t<0)t=0;
 if(t>len)t=len;
 x=x1+(int)(t*dx/len);y=y1+(int)(t*dy/len);
 dx=bx/Q-x;dy=by/Q-y;
 if(dx < -5||dx>5||dy < -5||dy>5)return 0;
 dd=dx*dx+dy*dy;if(dd>=25)return 0;
 if(!dd){dx=0;dy=-1;dd=1;}n=root(dd);if(!n)n=1;
 bx=x*Q+(int)((long)dx*6*Q/n);by=y*Q+(int)((long)dy*6*Q/n);
 reflect(dx,dy,n,0);
 if(active&&dy<=0){vy=-112;vx=side*30;++flips;}
 return 1;
}
static void step(void){int i,j;
 if(leftkey){if(la<4)++la;}else if(la>0)--la;
 if(rightkey){if(ra<4)++ra;}else if(ra>0)--ra;
 if(!live)return;
 for(j=0;j<4&&live;++j){
  vy=limit(vy+1,112);bx+=vx;by+=vy;
  if(bx<8*Q){bx=8*Q;if(vx<0)vx=-vx;}
  if(bx>136*Q){bx=136*Q;if(vx>0)vx=-vx;}
  if(by<8*Q){by=8*Q;if(vy<0)vy=-vy;}
  for(i=0;i<3;++i)if(circle(bumpx[i],bumpy[i],11)){
   if(score<999990L)score+=10;
   ++hits;
  }
  segment(5,85,33,113,0,0);segment(139,85,111,113,0,0);
  segment(33,113,63,121-la*4,leftkey,1);
  segment(111,113,81,121-ra*4,rightkey,-1);
  if(by>136*Q){--balls;++drains;ready();}
 }
}
