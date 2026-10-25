#!/usr/bin/env python3
"""Host controls for the PC1512 native capture checker; no driver/emulator."""
from pathlib import Path
import importlib.machinery,tempfile,unittest
C=importlib.machinery.SourceFileLoader('p15_capture_cmp',str(Path(__file__).with_name('P15CMP.PY'))).load_module()

def raw_marker(k):
    b=bytearray([255])*64000
    for y in range(144,147 if k==7 else 146):
        for x in range(4,45):
            at=(y&1)*8000+(y//2)*80+x//8
            for p in range(4):b[p*16000+at]&=255^(0x80>>(x&7))
    if k==3:
        at=(144//2)*80+100//8
        for p in range(4):b[p*16000+at]&=255^(0x80>>(100&7))
    return b

def fixture(root):
    lines=['VERSION=8','PC1512_PLANES=4','REAL_MODE=1','SCREEN_WIDTH=640','SCREEN_HEIGHT=200','NUMCOLORS=16','SHOTS=0','MULTIPLIER=1','FREE_BEFORE_PROBE=200000']
    for i,name in enumerate(C.NAMES,1):
        lines+=['CLEAR_SUCCESS=1','STAGE='+str(i),'NAME='+name]
        steps={'visible_steps':17,'marker_steps':9,'polylines':3}.get(name,0)
        if name in C.RR.APPS:lines+=['APP_FOUND=1','TITLE='+name,'LAUNCH_TO_PAINTED_MS=100','REPAINT_MS=55']+['REPAINT_MS=55']*2
        else:
            count={'roundrect_large':6,'ellipse_12':4,'scan_full':20000,'scan_narrow':20000}.get(name,steps or 20)
            lines+=['KIND=1','COUNT='+str(count),'API_SUCCESSES='+str(count),'ELAPSED_MS=100']
        for _ in range(2 if name=='cursor_overlap' else 1):lines+=['DUMP_CREATED=1','PLANE_STATE=3','CAPTURE_READ_PLANES=15','DUMP_BYTES=64000']
        raw=bytearray([255])*64000
        if name in ('scan_full','scan_narrow'):
            left,right=(0,640) if name=='scan_full' else (304,320)
            for y in range(100,120):
                for p in range(4):
                    at=p*16000+(y&1)*8000+(y//2)*80
                    raw[at+left//8:at+right//8]=bytes((right-left)//8)
            lines+=['RAW_OUTPUT_FOUND=1','SCAN_VISIBLE_ON_RETURN=1']
        (root/('RB%02d.BIN'%i)).write_bytes(raw)
        if steps:
            lines+=['STEP_DUMPS='+str(steps)]
            for k in range(1,steps+1):
                lines+=['STEP_DUMP_CREATED=1','PLANE_STATE=3','CAPTURE_READ_PLANES=15','STEP_DUMP_BYTES=64000']
                prefix={'visible_steps':'RV','marker_steps':'RM','polylines':'RP'}[name]
                (root/(prefix+'%02d.BIN'%k)).write_bytes(raw_marker(k) if name=='marker_steps' else bytes([255])*64000)
        if name=='marker_steps':
            lines+=['RAW_OUTPUT_FOUND=1','IDLE_VRAM_NOW=1','IDLE_VRAM_LATER=1','IDLE_BIOS_TICKS=9']
            for key in ['FIRST_ROW_ON_RETURN','SECOND_ROW_ON_RETURN','ROWS_VISIBLE_BEFORE_SETTLE']:lines += [key+'=1']*9
        if name=='polylines':lines+=['RAW_OUTPUT_FOUND=1']+['POLY_VISIBLE_ON_RETURN=1']*3
    lines+=['COMPLETE=1']
    text='\r\n'.join(lines)+'\r\n';(root/'RRBENCH.LOG').write_bytes(text.encode());return text

class Controls(unittest.TestCase):
    def test_distinct_planes_banks_and_edges(self):
        b=bytearray(64000)
        for p,x,y in [(0,0,0),(1,639,199),(2,7,1),(3,632,198)]:b[p*16000+(y&1)*8000+(y//2)*80+x//8]|=0x80>>(x&7)
        px=C.pixels(b)
        self.assertEqual([px[y*640+x] for _,x,y in [(0,0,0),(1,639,199),(2,7,1),(3,632,198)]],[1,2,4,8])
        self.assertEqual(sum(v!=0 for v in px),4)
        with self.assertRaises(ValueError):C.pixels(bytes(32768))

    def test_complete_and_failing_controls(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);text=fixture(root)
            self.assertEqual(C.validate(root)[3],[])
            cases=[('CAPTURE_READ_PLANES=15','CAPTURE_READ_PLANES=1'),('COUNT=20','COUNT=0'),('ELAPSED_MS=100','ELAPSED_MS=oops'),('REPAINT_MS=55','REPAINT_MS=oops'),('LAUNCH_TO_PAINTED_MS=100','LAUNCH_TO_PAINTED_MS=oops'),('MULTIPLIER=1','MULTIPLIER=0'),('PLANE_STATE=3','PLANE_STATE=1'),('FIRST_ROW_ON_RETURN=1','FIRST_ROW_ON_RETURN=0')]
            for old,new in cases:
                with self.subTest(fault=new):
                    (root/'RRBENCH.LOG').write_text(text.replace(old,new,1))
                    self.assertTrue(C.validate(root)[3])
            (root/'RRBENCH.LOG').write_text(text)
            p=root/'RB01.BIN';p.write_bytes(bytes(32768));self.assertTrue(C.validate(root)[3]);p.unlink();self.assertTrue(C.validate(root)[3])

if __name__=='__main__':unittest.main()
