/* Integer-only oval scenes. All caller dimensions160..640 x100..480.
 * Rotated outlines are application-generated33-point closed polylines.
 * Angle0 uses ordinary GDI Ellipse. This is not driver rotated-curve support. */
typedef struct {int cx,cy,rx,ry,angle,color,aspectX,aspectY;} FXOval;
static int fxSine[64]={0,13,25,37,49,60,71,81,90,99,106,113,118,123,126,127,
128,127,126,123,118,113,106,99,90,81,71,60,49,37,25,13,
0,-13,-25,-37,-49,-60,-71,-81,-90,-99,-106,-113,-118,-123,-126,-127,
-128,-127,-126,-123,-118,-113,-106,-99,-90,-81,-71,-60,-49,-37,-25,-13};
static int fxScale(int a,int b,int d){return (int)((long)a*b/d);}
static int fxAbs(int a){return a<0?-a:a;}
/* Density is a motion cadence; ribbons/vortex retain twice as many ovals. */
static int fxCount(int scene,int density){return scene==0||scene==2?density*2:scene==4?(density<8?density+2:8):density;}
static void fxShape(int scene,int phase,int index,int count,int w,int h,FXOval _far *o){int p,q,r,lat,dy;
 p=phase&63;o->cx=w/2;o->cy=h/2;o->angle=0;o->color=index&7;
 o->rx=w/4;o->ry=h/4;o->aspectX=w;o->aspectY=h;
 if(scene==0){ /* Intertwined turning ribbons. */
  q=(p+index*64/count)&63;
  o->cx+=fxScale(fxSine[q],w,1024);o->cy+=fxScale(fxSine[(q*2)&63],h,1024);
  o->rx=w/4+fxScale(fxSine[(q+16)&63],w,2048);o->ry=h/6;
  o->angle=(p+index*3)&63;o->color=index*3/count==0?5:index*3/count==1?2:3;
 }else if(scene==1){ /* Latitude rings plus turning meridians. */
  r=count/2;
  if(index<r){lat=(index+1)*32/(r+1)-16;
   o->cy+=fxScale(fxSine[lat&63],h,384);
   o->rx=fxScale(fxSine[(lat+16)&63],w,384);o->ry=h/30;
  }else{q=(p+(index-r)*32/(count-r))&63;
   o->rx=fxScale(fxAbs(fxSine[q]),w,384);o->ry=h/3;
   o->angle=0;
  }
  /* Uniform display-aspect tilt of center offsets and ring axes. */
  dy=o->cy-h/2;o->cx=w/2-fxScale(fxScale(dy,fxSine[6],128),w,h);
  o->cy=h/2+fxScale(dy,fxSine[22],128);o->angle=6;
 }else if(scene==2){ /* Nested overlapping vortex. */
  q=(p+index*5)&63;r=count-index+2;
  o->rx=w*r/(3*(count+3));o->ry=h*r/(5*(count+3));
  o->cx+=fxScale(fxSine[q],w,1536);o->cy+=fxScale(fxSine[(q+16)&63],h,1536);
  o->angle=(p+index*2)&63;o->color=index&1;
 }else if(scene==3){ /* Offset receding tunnel, rings wrap near the center. */
  q=(index*64/count+p)&63;r=q+8;
  o->rx=fxScale(w,r,160);o->ry=fxScale(h,r,160);
  o->cx+=fxScale(fxScale(fxSine[p],72-r,128),w,512);
  o->cy+=fxScale(fxScale(fxSine[(p+16)&63],72-r,128),h,512);
  o->color=r<24?3:r<48?2:5;
 }else{ /* Three extremely flat oval floor contours; no straight artwork. */
  if(index<3){r=h/36;if(r<3)r=3;o->cy=h*7/8+index*r;
   o->rx=w*3/8-index*w/32;o->ry=1;o->color=6;
  }else{q=(p-(index-3)*2)&31;r=q<16?q:32-q;
   o->rx=w/20;o->ry=h/14;
   if(r<3){o->rx=o->rx*(11-r)/8;o->ry=o->ry*(5+r)/8;}
   o->cx=w/2+fxScale(fxSine[(p-(index-3)*2)&63],w,384);
   o->cy=h*7/8-o->ry-fxScale(q*(32-q),h,512);
   o->color=1-((index-3)&1);
  }
 }
 if(o->rx<2)o->rx=2;if(o->ry<2&&!(scene==4&&index<3))o->ry=2;
}
/* No multiplication of two screen coordinates; largest product < 2^24. */
static void fxVertex(const FXOval _far *o,int vertex,int _far *x,int _far *y){int p=(vertex*2)&63,a,b;
 a=fxScale(fxSine[(p+16)&63],o->rx,128);b=fxScale(fxSine[p],o->ry,128);
 *x=o->cx+fxScale(a,fxSine[(o->angle+16)&63],128)-fxScale(fxScale(b,fxSine[o->angle],128),o->aspectX,o->aspectY);
 *y=o->cy+fxScale(fxScale(a,fxSine[o->angle],128),o->aspectY,o->aspectX)+fxScale(b,fxSine[(o->angle+16)&63],128);
}
