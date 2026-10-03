/* 40 independent heights + velocities, Q4 pixels. No float or heap. */
#define SAMPLES 40
static int dirty;
static int height[SAMPLES], velocity[SAMPLES], nextV[SAMPLES];
static int bound(int v,int lo,int hi) { if(hi<lo)hi=lo;return v<lo?lo:(v>hi?hi:v); }
static void step(int acceleration) {
 int i,left,right,lap,v,oldPixel;
 dirty=0;
 acceleration=bound(acceleration,-24,24);
 for(i=0;i<SAMPLES;i++){
  left=height[i?i-1:0];right=height[i<SAMPLES-1?i+1:SAMPLES-1];
  lap=left+right-2*height[i];
  /* Right acceleration raises left side (negative screen Y). */
  v=velocity[i]+acceleration*(2*i-(SAMPLES-1))/16-height[i]/16+lap/8;
  nextV[i]=bound(v*7/8,-128,128);
 }
 for(i=0;i<SAMPLES;i++){
  oldPixel=height[i]/16;
  velocity[i]=nextV[i];height[i]=bound(height[i]+velocity[i],-512,512);
  /* Remove sub-two-pixel fixed-point stiction smoothly. */
  if(!velocity[i]&&height[i]>-32&&height[i]<32)height[i]=height[i]*15/16;
  if(height[i]>=-2&&height[i]<=2&&velocity[i]>=-1&&velocity[i]<=1)
   height[i]=velocity[i]=0;
  if(oldPixel!=height[i]/16)dirty=1;
 }
}
