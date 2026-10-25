"""Host controls for the ColorPlus native probe; no emulator."""
from pathlib import Path
import importlib.machinery,tempfile,unittest
HERE=Path(__file__).resolve().parent
C=importlib.machinery.SourceFileLoader('cp_cmp_control',str(HERE/'CPCMP.PY')).load_module()
P=importlib.machinery.SourceFileLoader('cp_hw_model',str(HERE/'PCPPATCH.PY')).load_module()

def raster(points=()):
    shadow=bytearray([255])*32000
    for x,y in points:
        for plane in range(4):shadow[y*160+plane*40+x//8]&=255^(128>>(x&7))
    raw=P.model_flush(shadow)
    for bank in range(4):raw[bank*8192+8000]=1<<bank
    return raw

def fixture(root):
    lines=['VERSION=9','COLORPLUS_PLANES=2','REAL_MODE=1','LOGICAL_WIDTH=320','LOGICAL_HEIGHT=200','SCREEN_WIDTH=320','SCREEN_HEIGHT=200','NUMCOLORS=16','SHOTS=0','MULTIPLIER=1','FREE_BEFORE_PROBE=200000']
    white=raster()
    for i,name in enumerate(C.NAMES,1):
        lines+=['CLEAR_SUCCESS=1','STAGE='+str(i),'NAME='+name]
        steps={'visible_steps':17,'marker_steps':9,'polylines':3}.get(name,0)
        if name in C.RR.APPS:lines+=['APP_FOUND=1','TITLE='+name,'LAUNCH_TO_PAINTED_MS=100']+['REPAINT_MS=55']*3
        else:
            count={'roundrect_large':6,'ellipse_12':4,'scan_full':20000,'scan_narrow':20000}.get(name,steps or 20)
            lines+=['KIND=1','COUNT='+str(count),'API_SUCCESSES='+str(count),'ELAPSED_MS=100']
        for _ in range(2 if name=='cursor_overlap' else 1):lines+=['DUMP_CREATED=1','BANK_STATE=15','CAPTURE_BANKS=15','DUMP_BYTES=32768']
        raw=white
        if name in ('scan_full','scan_narrow'):
            left,right=(0,320) if name=='scan_full' else (144,160)
            raw=raster((x,y) for y in range(100,120) for x in range(left,right))
            lines+=['RAW_OUTPUT_FOUND=1','SCAN_VISIBLE_ON_RETURN=1']
        (root/('RB%02d.BIN'%i)).write_bytes(raw)
        if steps:
            lines+=['STEP_DUMPS='+str(steps)]
            for k in range(1,steps+1):
                lines+=['STEP_DUMP_CREATED=1','BANK_STATE=15','CAPTURE_BANKS=15','STEP_DUMP_BYTES=32768']
                prefix={'visible_steps':'RV','marker_steps':'RM','polylines':'RP'}[name]
                if name=='marker_steps':
                    points=[(x,y) for y in range(144,147 if k==7 else 146) for x in range(4,45)]
                    if k==3:points.append((100,144))
                    data=raster(points)
                else:data=white
                (root/(prefix+'%02d.BIN'%k)).write_bytes(data)
        if name=='marker_steps':
            lines+=['RAW_OUTPUT_FOUND=1','IDLE_VRAM_NOW=1','IDLE_VRAM_LATER=1','IDLE_BIOS_TICKS=9']
            for key in ('FIRST_ROW_ON_RETURN','SECOND_ROW_ON_RETURN','ROWS_VISIBLE_BEFORE_SETTLE'):lines += [key+'=1']*9
        if name=='polylines':lines+=['RAW_OUTPUT_FOUND=1']+['POLY_VISIBLE_ON_RETURN=1']*3
    lines+=['COMPLETE=1'];text='\r\n'.join(lines)+'\r\n'
    (root/'RRBENCH.LOG').write_bytes(text.encode());return text

class Controls(unittest.TestCase):
    def test_decoder_all_colours_and_edges(self):
        shadow=bytes(((i*73+i//160)&255) for i in range(32000));raw=P.model_flush(shadow)
        actual=C.pixels(raw)
        self.assertEqual(actual,bytes(P.shadow_pixel(shadow,y,x) for y in range(200) for x in range(320)))
        self.assertEqual(set(actual),set(range(16)))
        with self.assertRaises(ValueError):C.pixels(bytes(16384))
        self.assertNotEqual(C.pixels(raw[16384:]+raw[:16384]),actual)
        self.assertNotEqual(C.pixels(raw[8192:16384]+raw[:8192]+raw[24576:]+raw[16384:24576]),actual)
    def test_complete_and_negative_controls(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);a=root/'A';b=root/'B';a.mkdir();b.mkdir();text=fixture(a);fixture(b)
            self.assertEqual(C.validate(a)[3],[]);self.assertTrue(C.compare(a,b)['pass'])
            for old,new in [('COMPLETE=1','COMPLETE=0'),('SCREEN_WIDTH=320','SCREEN_WIDTH=640'),('LOGICAL_HEIGHT=200','LOGICAL_HEIGHT=400'),('CAPTURE_BANKS=15','CAPTURE_BANKS=3'),('BANK_STATE=15','BANK_STATE=3'),('COUNT=20','COUNT=0'),('ELAPSED_MS=100','ELAPSED_MS=nope'),('REPAINT_MS=55','REPAINT_MS=nope'),('FIRST_ROW_ON_RETURN=1','FIRST_ROW_ON_RETURN=0')]:
                (a/'RRBENCH.LOG').write_bytes(text.replace(old,new,1).encode());self.assertTrue(C.validate(a)[3],new)
            (a/'RRBENCH.LOG').write_bytes(text.encode())
            p=a/'RB01.BIN';saved=p.read_bytes();p.write_bytes(saved[:16384]);self.assertTrue(C.validate(a)[3]);p.write_bytes(saved)
            bad=bytearray(saved);bad[8000]^=1;p.write_bytes(bad);self.assertTrue(C.validate(a)[3]);p.write_bytes(saved)
            p=a/'RM01.BIN';saved=p.read_bytes();bad=bytearray(saved);bad[(144//2)*80+44//4]^=1<<(6-2*(44&3));p.write_bytes(bad)
            self.assertTrue(C.validate(a)[3]);self.assertFalse(C.compare(a,a)['pass']);p.write_bytes(saved)
            p=a/'RB11.BIN';saved=p.read_bytes();bad=bytearray(saved);bad[(119&1)*8192+(119//2)*80+319//4]^=1<<(6-2*(319&3));p.write_bytes(bad)
            self.assertTrue(C.validate(a)[3]);p.write_bytes(saved)
            p=a/'RV01.BIN';p.unlink();self.assertTrue(C.validate(a)[3])
    def test_probe_capture_source(self):
        generator=importlib.machinery.SourceFileLoader('cp_capture_source',str(HERE/'CPBENCH.PY')).load_module()
        with tempfile.TemporaryDirectory() as temp:
            source=Path(temp)/'source';generator.emit(source)
            text=(source/'RRBENCH.C').read_text()
        self.assertIn('static BYTE chunk[8192]',text);self.assertIn('bank < 4',text)
        self.assertIn('at + 16384U',text);self.assertNotIn('p15dump',text)
        self.assertNotIn('outp(',text);self.assertIn('COLORPLUS_PLANES',text)
        self.assertIn('scanstage("scan_full",0,320)',text)
        self.assertLess(text.index('_asm popf',text.index('_fmemcpy')),text.index('total += _lwrite'))
if __name__=='__main__':unittest.main()
