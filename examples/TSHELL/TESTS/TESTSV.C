#include "../SVCORE.H"
#include <assert.h>
#include <stdio.h>
int main(void){SVSTATE s={0,0,0};
assert(!SvDue(&s,100,1,10000,1)); assert(!SvDue(&s,10099,1,10000,1)); assert(SvDue(&s,10100,1,10000,1));
assert(!SvDue(&s,10100,1,10000,1));assert(!SvDue(&s,20100,2,10000,1));assert(!SvDue(&s,30100,2,10000,0));assert(!SvDue(&s,40099,2,10000,1));assert(SvDue(&s,40100,2,10000,1));
SvReset(&s,0xfffffff0U,0xffffffffU);assert(!SvDue(&s,0x26ffU,0xffffffffU,10000,1));assert(SvDue(&s,0x2700U,0xffffffffU,10000,1));
assert(!SvDue(&s,0x4e20U,0,10000,1));assert(SvDue(&s,0x7530U,0,10000,1));puts("PASS: deadline boundary, once per interval, activity reset, blocked reset, 32-bit timer wrap, generation wrap");return 0;}
