#include <stdio.h>
#include <assert.h>
#include "WATER.H"
int main(void){int i,t,max=0,flip=0;step(24);assert(height[0]<0&&height[39]>0);for(t=0;t<500;t++){step(0);if(height[0]>0)flip=1;}assert(flip);for(i=0;i<40;i++)assert(height[i]>=-15&&height[i]<=15);for(t=0;t<100000;t++){step((t*31%49)-24);for(i=0;i<40;i++){assert(height[i]>=-512&&height[i]<=512);assert(velocity[i]>=-128&&velocity[i]<=128);if(height[i]>max)max=height[i];}}for(t=0;t<500;t++)step(0);for(i=0;i<40;i++)assert(height[i]>=-15&&height[i]<=15);printf("PASS direction, rebound, damping, 100000 stress ticks; peak %d Q4\n",max);return 0;}
