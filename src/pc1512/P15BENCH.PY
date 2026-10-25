#!/usr/bin/env python3
"""Emit/build the existing RRBENCH with PC1512 capture and visibility probes.

Only the test application changes. Frames contain plane 0..3, each with
8,000 visible even-row bytes followed by 8,000 visible odd-row bytes.
No packed-pixel or XR1 panning probe is used. Read selection is restored to 0.
"""
from pathlib import Path
import argparse,hashlib,importlib.machinery,json,sys
HERE=Path(__file__).resolve().parent
RR=HERE.parent/'rrect'

CAPTURE=r'''
#include <conio.h>
#include <string.h>
#pragma intrinsic(outp)
static void line(char *, long);
/* Two undisplayed padding bytes test write-only plane registers without
 * claiming that IN from those ports reads their state. Sentinel setup is
 * outside timing. A write with the driver's current mask must reach all
 * four planes; a read before selecting anything must see plane zero.
 */
static void p15init(void)
{
    int plane;
    volatile BYTE FAR *v = (volatile BYTE FAR *)0xb8000000L;
    _asm pushf
    _asm cli
    for (plane = 0; plane < 4; plane++) {
        outp(0x3dd, 1 << plane);
        v[8000] = (BYTE)(1 << plane); v[8001] = 0;
    }
    outp(0x3dd, 15); outp(0x3de, 0);
    _asm popf
}
static int p15state(void)
{
    int plane, state = 0, all = 1;
    volatile BYTE FAR *v = (volatile BYTE FAR *)0xb8000000L;
    _asm pushf
    _asm cli
    if (v[8000] == 1) state |= 1;
    v[8001] = 0xa5;
    for (plane = 0; plane < 4; plane++) {
        outp(0x3de, plane);
        if (v[8001] != 0xa5) all = 0;
    }
    if (all) state |= 2;
    outp(0x3dd, 15); v[8001] = 0; outp(0x3de, 0);
    _asm popf
    return state;
}
static unsigned p15dump(HFILE h)
{
    static BYTE bank[8000];
    int plane, parity, selected = 0;
    unsigned total = 0;
    volatile BYTE FAR *video = (volatile BYTE FAR *)0xb8000000L;
    line("PLANE_STATE", p15state());
    for (plane = 0; plane < 4; plane++) {
        _asm pushf
        _asm cli
        outp(0x3de, plane);
        if ((unsigned)video[8000] == (1U << plane)) selected |= 1 << plane;
        outp(0x3de, 0);
        _asm popf
        for (parity = 0; parity < 2; parity++) {
            /* A cursor IRQ restores read selection to zero. Copy with
             * saved FLAGS/CLI, restore selection, then allow DOS I/O.
             */
            _asm pushf
            _asm cli
            outp(0x3de, plane);
            _fmemcpy((LPSTR)bank, (LPSTR)(video + parity * 8192U), 8000);
            outp(0x3de, 0);
            _asm popf
            total += _lwrite(h, (LPSTR)bank, 8000);
        }
    }
    outp(0x3de, 0);
    line("CAPTURE_READ_PLANES", selected);
    return total;
}
static int p15black(int x, int y)
{
    int plane, color = 0, state = p15state();
    unsigned at = (y & 1) * 8192 + (y >> 1) * 80 + (x >> 3);
    volatile BYTE FAR *video = (volatile BYTE FAR *)0xb8000000L;
    _asm pushf
    _asm cli
    for (plane = 0; plane < 4; plane++) {
        outp(0x3de, plane);
        if (video[at] & (0x80 >> (x & 7))) color |= 1 << plane;
    }
    outp(0x3de, 0);
    _asm popf
    return color == 0 && state == 3;
}
'''

POLY=r'''
/* Matched direct scanlines isolate copy costs from BEGIN/END marker savings.
 * In particular, full-width Output previously used FlushRetainRows.
 */
static void scanstage(char *name, int left, int right)
{
    typedef int (FAR PASCAL *OUTPROC)(LPSTR,int,int,POINT FAR *,LPSTR,LPSTR,LPSTR,RECT FAR *);
    OUTPROC output;
    POINT pts[2];
    int device = 1, mode[16], pen[3], i, k;
    long ok = 0;
    DWORD t0, t1;
    output = (OUTPROC)GetProcAddress(GetModuleHandle("DISPLAY"), MAKEINTRESOURCE(8));
    for (i = 0; i < 16; i++) mode[i] = 0;
    for (i = 0; i < 3; i++) pen[i] = 0;
    mode[0] = R2_COPYPEN; mode[1] = OPAQUE;
    pts[0].x = 0; pts[1].x = left; pts[1].y = right;
    seq++; clear();
    line("STAGE", seq); _lwrite(logFile,"NAME=",5);
    _lwrite(logFile,name,lstrlen(name)); _lwrite(logFile,"\r\n",2);
    line("KIND", 5); line("COUNT", 20000L * mult);
    line("RAW_OUTPUT_FOUND", output != NULL); flush();
    if (!output) return;
    t0 = GetTickCount();
    for (k = 0; k < mult; k++) for (i = 0; i < 20000; i++) {
        pts[0].y = 100 + i % 20;
        ok += output((LPSTR)&device,4,2,pts,(LPSTR)pen,NULL,(LPSTR)mode,NULL) != 0;
    }
    t1 = GetTickCount();
    line("SCAN_VISIBLE_ON_RETURN", p15black(left,119) && p15black(right-1,119));
    line("ELAPSED_MS", t1-t0); line("API_SUCCESSES", ok);
    dump(); flush();
}

/* Actual ordinal-8 calls: two/three/1024-point polylines, including edges.
 * Probe the first pixel on return, before a dump, marker or any other GDI.
 */
static void polystage(void)
{
    typedef int (FAR PASCAL *OUTPROC)(LPSTR,int,int,POINT FAR *,LPSTR,LPSTR,LPSTR,RECT FAR *);
    OUTPROC output;
    static POINT pts[1024];
    int device = 1, mode[16], pen[3], k, i, count, ok = 0;
    DWORD t0 = GetTickCount();
    output = (OUTPROC)GetProcAddress(GetModuleHandle("DISPLAY"), MAKEINTRESOURCE(8));
    for (i = 0; i < 16; i++) mode[i] = 0;
    for (i = 0; i < 3; i++) pen[i] = 0;
    mode[0] = R2_COPYPEN; mode[1] = OPAQUE;
    seq++;
    line("STAGE", seq);
    _lwrite(logFile, "NAME=polylines\r\n", 16);
    line("KIND", 5); line("COUNT", 3);
    line("RAW_OUTPUT_FOUND", output != NULL);
    if (!output) { flush(); return; }
    for (k = 1; k <= 3; k++) {
        clear();
        count = k == 1 ? 2 : (k == 2 ? 3 : 1024);
        for (i = 0; i < count; i++) {
            pts[i].x = i % 640;
            pts[i].y = 80 + i % 3;
        }
        if (k == 1) { pts[1].x = 639; pts[1].y = 80; }
        if (k == 2) { pts[1].x = 639; pts[1].y = 81; pts[2].x = 632; pts[2].y = 85; }
        ok += output((LPSTR)&device,18,count,pts,(LPSTR)pen,NULL,(LPSTR)mode,NULL) != 0;
        line("POLY_VISIBLE_ON_RETURN", p15black(0,80));
        framedump(k, 2);
    }
    line("ELAPSED_MS", GetTickCount() - t0);
    line("API_SUCCESSES", ok); line("STEP_DUMPS", 3);
    dump(); flush();
}
'''

def emit(out):
    out.mkdir(parents=True,exist_ok=False)
    t=(RR/'RRBENCH.C').read_text()
    def change(old,new,count=1):
        nonlocal t
        if t.count(old)!=count:raise SystemExit('P15BENCH anchor count: '+old[:70])
        t=t.replace(old,new)
    change('#include <windows.h>','#include <windows.h>\n'+CAPTURE)
    change('_lwrite(h, (LPSTR)0xb8000000L, 0x8000U)','p15dump(h)',2)
    change("if (marker) n[4] = 'M';","if (marker) n[4] = (char)(marker == 2 ? 'P' : 'M');")
    change('(((volatile BYTE FAR *)0xb8000000L)[at] & 15) == 0','p15black(4,144)',2)
    change('(((BYTE FAR *)0xb8000000L)[at] & 15) == 0','p15black(4,144)')
    change('if (k == 6) setpan();','if (k == 6) output((LPSTR)&device,81,0,NULL,NULL,NULL,NULL,NULL);')
    change('        pts[0].y++;\n        b = output',
           '        line("FIRST_ROW_ON_RETURN", p15black(4,144));\n        pts[0].y++;\n        b = output')
    change('        at = (144 / 4) * 160 + 2;',
           '        line("SECOND_ROW_ON_RETURN", p15black(4,145));\n        at = (144 / 4) * 160 + 2;')
    change('    {1, 0, 0, 0, 0, 8, 1, 3, R2_COPYPEN, 2}',
           '    {2, 0, 170, 640, 8, 0, 1, 3, R2_COPYPEN, 0},\n'
           '    {1, 0, 80, 16, 12, 8, 1, 3, R2_COPYPEN, 0},\n'
           '    {1, 624, 100, 16, 12, 8, 1, 3, R2_COPYPEN, 0},\n'
           '    {1, 0, 0, 0, 0, 8, 1, 3, R2_COPYPEN, 2}')
    change('static void stepstage(void)',POLY+'\nstatic void stepstage(void)')
    change('    steps[NSTEPS - 1].x = width - 15;','    steps[8].x = width + 80;\n    steps[NSTEPS - 1].x = width - 15;')
    change('        x = 4 + (j % cols) * dx;','        x = w == width ? 0 : 4 + (j % cols) * dx;')
    change('line("VERSION", xr ? (panonly ? 7 : 6) : 4);','line("VERSION", 8);\n    line("PC1512_PLANES", 4);\n    line("REAL_MODE", !(GetWinFlags() & WF_PMODE));')
    change('    line("MULTIPLIER", mult);','    line("MULTIPLIER", mult);\n    line("FREE_BEFORE_PROBE", GetFreeSpace(0));')
    change('    oldcur = SetCursor(NULL);','    oldcur = SetCursor(NULL);\n    p15init();')
    change('        cursorstage();','        batch("full_width", 2, width, 20, 0, 0, blackPen, ltgray, R2_COPYPEN, 20, 0, 0, 0);\n        scanstage("scan_full",0,640);\n        scanstage("scan_narrow",304,320);\n        cursorstage();')
    change('        if (xr) markerstage();','        markerstage();\n        polystage();')
    (out/'RRBENCH.C').write_bytes(t.replace('\n','\r\n').encode('ascii'))
    for name in ('RRBENCH.DEF','RRBENCH.RSP'):(out/name).write_bytes((RR/name).read_bytes())
    build=(RR/'BUILD.BAT').read_text().replace('SET INCLUDE=C:\\DDK\\286\\INC','SET INCLUDE=C:\\DDK\\286\\INC;C:\\INCLUDE')
    (out/'BUILD.BAT').write_bytes(build.replace('\n','\r\n').encode('ascii'))
    (out/'P15EMIT.JSN').write_text(json.dumps({'base_rrbench_sha256':hashlib.sha256((RR/'RRBENCH.C').read_bytes()).hexdigest(),
        'generated_sha256':hashlib.sha256((out/'RRBENCH.C').read_bytes()).hexdigest(),'frame_bytes':64000},indent=2)+'\n')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--emit',type=Path,required=True)
    p.add_argument('--build',type=Path)
    p.add_argument('--repo',type=Path)
    p.add_argument('--dosbox',type=Path)
    p.add_argument('--lease',type=Path)
    a=p.parse_args();emit(a.emit)
    if a.build:
        if not all((a.repo,a.dosbox,a.lease)):p.error('build requires --repo, --dosbox and --lease')
        rr=importlib.machinery.SourceFileLoader('p15_rrapp',str(RR/'RRAPP.PY')).load_module()
        rr.HERE=a.emit.resolve()
        return rr.main(['--repo',str(a.repo),'--dosbox',str(a.dosbox),'--out',str(a.build),'--lease',str(a.lease)])
    return 0

if __name__=='__main__':sys.exit(main())
