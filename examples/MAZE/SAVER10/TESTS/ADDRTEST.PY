#!/usr/bin/env python3
"""Enumerate the actual eight-pixel column writes for all five profiles."""
profiles=[(160,0,2),(320,0,4),(320,1,2),(640,2,4),(640,3,2)]
for width,kind,banks in profiles:
    n=width//8
    bpc=4 if kind==0 else 1 if kind==3 else 2
    touched=[(y&(banks-1))*8192+(y//banks)*(160 if banks==4 else 80)+stripe*bpc+j for stripe in range(n) for y in range(200) for j in range(bpc)]
    assert len(set(touched))==len(touched)
    assert min(touched)==0 and max(touched)<banks*8192
    print('PASS width=%d kind=%d banks=%d unique_bytes=%d maximum_offset=%d capacity=%d' % (width,kind,banks,len(touched),max(touched),banks*8192))
