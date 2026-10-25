#!/usr/bin/env python3
"""Emit/build the existing RRBENCH with fixed ColorPlus capture and visibility probes.

Only the test application changes. Captures contain all 32768 B800h bytes,
two directly mapped 16K ColorPlus planes, including all four bank paddings.
No PC1512 read-plane interface, packed Tandy decoder or panning is used.
"""
from pathlib import Path
import argparse,hashlib,importlib.machinery,json,sys
HERE=Path(__file__).resolve().parent
RR=HERE.parent/'rrect'

CAPTURE=r'''
#include <string.h>
static void line(char *, long);
/* ColorPlus maps two 16K planes directly. Distinct private padding bytes
 * calibrate all four 8K banks and detect plain-CGA aliasing. No I/O port
 * register is written or inferred from an unsupported register read.
 */
static void cpinit(void)
{
    int bank;
    volatile BYTE FAR *v = (volatile BYTE FAR *)0xb8000000L;
    _asm pushf
    _asm cli
    for (bank = 0; bank < 4; bank++) v[bank * 8192U + 8000U] = (BYTE)(1U << bank);
    _asm popf
}
static int cpstate(void)
{
    int bank, state = 0;
    volatile BYTE FAR *v = (volatile BYTE FAR *)0xb8000000L;
    _asm pushf
    _asm cli
    for (bank = 0; bank < 4; bank++)
        if (v[bank * 8192U + 8000U] == (BYTE)(1U << bank)) state |= 1 << bank;
    _asm popf
    return state;
}
static unsigned cpdump(HFILE h)
{
    static BYTE chunk[8192];
    int bank, copied = 0;
    unsigned total = 0;
    volatile BYTE FAR *video = (volatile BYTE FAR *)0xb8000000L;
    line("BANK_STATE", cpstate());
    for (bank = 0; bank < 4; bank++) {
        /* Saved FLAGS/CLI prevents cursor IRQ changes during each copy.
         * DOS sees the scratch buffer with interrupts restored.
         */
        _asm pushf
        _asm cli
        _fmemcpy((LPSTR)chunk, (LPSTR)(video + bank * 8192U), 8192U);
        _asm popf
        if (chunk[8000] == (BYTE)(1U << bank)) copied |= 1 << bank;
        total += _lwrite(h, (LPSTR)chunk, 8192U);
    }
    line("CAPTURE_BANKS", copied);
    return total;
}
static int cpblack(int x, int y)
{
    int shift = 6 - 2 * (x & 3), black;
    unsigned at = (y & 1) * 8192U + (y >> 1) * 80U + (x >> 2);
    volatile BYTE FAR *v = (volatile BYTE FAR *)0xb8000000L;
    _asm pushf
    _asm cli
    black = (((v[at] >> shift) & 3) == 0 && ((v[at + 16384U] >> shift) & 3) == 0);
    _asm popf
    return black && cpstate() == 15;
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
    line("SCAN_VISIBLE_ON_RETURN", cpblack(left,119) && cpblack(right-1,119));
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
            pts[i].x = i % 320;
            pts[i].y = 80 + i % 3;
        }
        if (k == 1) { pts[1].x = 319; pts[1].y = 80; }
        if (k == 2) { pts[1].x = 319; pts[1].y = 81; pts[2].x = 312; pts[2].y = 85; }
        ok += output((LPSTR)&device,18,count,pts,(LPSTR)pen,NULL,(LPSTR)mode,NULL) != 0;
        line("POLY_VISIBLE_ON_RETURN", cpblack(0,80));
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
        if t.count(old)!=count:raise SystemExit('CPBENCH anchor count: '+old[:70])
        t=t.replace(old,new)
    change('#include <windows.h>','#include <windows.h>\n'+CAPTURE)
    change('_lwrite(h, (LPSTR)0xb8000000L, 0x8000U)','cpdump(h)',2)
    change("if (marker) n[4] = 'M';","if (marker) n[4] = (char)(marker == 2 ? 'P' : 'M');")
    change('(((volatile BYTE FAR *)0xb8000000L)[at] & 15) == 0','cpblack(4,144)',2)
    change('(((BYTE FAR *)0xb8000000L)[at] & 15) == 0','cpblack(4,144)')
    change('if (k == 6) setpan();','if (k == 6) output((LPSTR)&device,81,0,NULL,NULL,NULL,NULL,NULL);')
    change('        pts[0].y++;\n        b = output',
           '        line("FIRST_ROW_ON_RETURN", cpblack(4,144));\n        pts[0].y++;\n        b = output')
    change('        at = (144 / 4) * 160 + 2;',
           '        line("SECOND_ROW_ON_RETURN", cpblack(4,145));\n        at = (144 / 4) * 160 + 2;')
    change('    {1, 0, 0, 0, 0, 8, 1, 3, R2_COPYPEN, 2}',
           '    {2, 0, 0, 320, 1, 0, 1, 3, R2_COPYPEN, 0},\n'
           '    {2, 7, 1, 3, 1, 0, 1, 3, R2_COPYPEN, 0},\n'
           '    {2, 311, 198, 9, 2, 0, 1, 3, R2_COPYPEN, 0},\n'
           '    {1, 0, 0, 0, 0, 8, 1, 3, R2_COPYPEN, 2}')
    change('static void stepstage(void)',POLY+'\nstatic void stepstage(void)')
    change('    steps[NSTEPS - 1].x = width - 15;','    steps[8].x = width + 80;\n    steps[NSTEPS - 1].x = width - 15;')
    change('        x = 4 + (j % cols) * dx;','        x = w == width ? 0 : 4 + (j % cols) * dx;')
    change('line("VERSION", xr ? (panonly ? 7 : 6) : 4);','line("VERSION", 9);\n    line("COLORPLUS_PLANES", 2);\n    line("REAL_MODE", !(GetWinFlags() & WF_PMODE));')
    change('    line("MULTIPLIER", mult);','    line("MULTIPLIER", mult);\n    line("FREE_BEFORE_PROBE", GetFreeSpace(0));')
    change('    oldcur = SetCursor(NULL);','    oldcur = SetCursor(NULL);\n    cpinit();')
    change('        cursorstage();','        batch("full_width", 2, width, 20, 0, 0, blackPen, ltgray, R2_COPYPEN, 20, 0, 0, 0);\n        scanstage("scan_full",0,320);\n        scanstage("scan_narrow",144,160);\n        cursorstage();')
    change('        if (xr) markerstage();','        markerstage();\n        polystage();')
    (out/'RRBENCH.C').write_bytes(t.replace('\n','\r\n').encode('ascii'))
    for name in ('RRBENCH.DEF','RRBENCH.RSP'):(out/name).write_bytes((RR/name).read_bytes())
    build=(RR/'BUILD.BAT').read_text().replace('SET INCLUDE=C:\\DDK\\286\\INC','SET INCLUDE=C:\\DDK\\286\\INC;C:\\INCLUDE')
    (out/'BUILD.BAT').write_bytes(build.replace('\n','\r\n').encode('ascii'))
    (out/'CPEMIT.JSN').write_text(json.dumps({'base_rrbench_sha256':hashlib.sha256((RR/'RRBENCH.C').read_bytes()).hexdigest(),
        'generated_sha256':hashlib.sha256((out/'RRBENCH.C').read_bytes()).hexdigest(),'frame_bytes':32768},indent=2)+'\n')

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
