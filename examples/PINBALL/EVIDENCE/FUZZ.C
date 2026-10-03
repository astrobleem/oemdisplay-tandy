/* Host-only C99 physics review harness. No Windows or hardware coverage.
   Compile with -I pointing at examples/PINBALL, then run.
   Keeps schedules identical on 32-bit and 64-bit hosts. */
#include <stdio.h>
#include <stdint.h>
#include "PHYSICS.H"

static int bounded(void)
{
    return bx>=8*Q && bx<=136*Q && by>=0 && by<=136*Q &&
           vx>=-112 && vx<=112 && vy>=-112 && vy<=112 &&
           score>=0 && score<=999990L;
}

int main(void)
{
    int s,i,high,hold,mask,maxhigh=0;
    int oldx,oldy,still,maxstill;
    uint32_t rng;
    unsigned seed=5;

    reset();live=1;bx=42*Q;by=26*Q;vy=50;
    for(i=0;i<2000 && live && by<40*Q;i++)step();
    if(live && by<40*Q){puts("FAIL: vertical bumper loop");return 1;}
    printf("PASS: axis bumper loop escaped in %d ticks\n",i);

    for(mask=0;mask<5;mask++){
        reset();launch();still=maxstill=high=maxhigh=0;
        for(i=0;i<1000000;i++){
            if(!live){if(!balls)reset();launch();}
            if(mask==4){
                seed=(unsigned)((long)seed*109+89)&32767;
                leftkey=seed&1;rightkey=(seed>>4)&1;
            }else{leftkey=mask&1;rightkey=(mask>>1)&1;}
            oldx=bx;oldy=by;step();
            if(!bounded()){
                printf("FAIL: bounds mask=%d tick=%d x=%d y=%d\n",
                       mask,i,bx,by);return 1;
            }
            if(oldx==bx && oldy==by){
                ++still;if(still>maxstill)maxstill=still;
            }else still=0;
            if(by<95*Q){++high;if(high>maxhigh)maxhigh=high;}
            else high=0;
            if(still>1000 || high>1000){
                printf("FAIL: suspected trap mask=%d tick=%d\n",mask,i);
                return 1;
            }
        }
        printf("PASS: mask=%d 1000000 ticks, max unchanged=%d, max high=%d\n",
               mask,maxstill,maxhigh);
    }

    maxhigh=0;
    for(s=1;s<=200;s++){
        rng=(uint32_t)s;high=hold=mask=0;reset();launch();
        for(i=0;i<200000;i++){
            if(!live){if(!balls)reset();launch();high=0;}
            if(!hold--){
                rng^=rng<<13;rng^=rng>>17;rng^=rng<<5;
                mask=(int)(rng&3);hold=(int)((rng>>4)%40);
            }
            leftkey=mask&1;rightkey=(mask>>1)&1;step();
            if(!bounded()){
                printf("FAIL: bounds seed=%d tick=%d x=%d y=%d vx=%d vy=%d\n",
                       s,i,bx,by,vx,vy);return 1;
            }
            if(by<95*Q){++high;if(high>maxhigh)maxhigh=high;}
            else high=0;
            if(high>1000){
                printf("FAIL: suspected top trap seed=%d tick=%d x=%d y=%d\n",
                       s,i,bx,by);return 1;
            }
        }
    }
    printf("PASS: 40000000 fuzz ticks, 200 seeds, max high=%d ticks\n",maxhigh);
    puts("PASS: 45000000 total schedule ticks plus axis-loop regression");
    return 0;
}
