#!/usr/bin/env python3
"""Bounded host CGA checks. No emulator, compiler, native or timing claim."""
import argparse
import hashlib
import importlib.machinery
import json
import random
import re
import struct
import sys
import unittest
from pathlib import Path
import CGAMODEL as M
import CGAFONT as F
import STAGECGA as S

HERE = Path(__file__).resolve().parent


class Memory(unittest.TestCase):
    def test_all_pair_colors_and_addresses(self):
        # Independent pair formula: DEh foreground is the RIGHT half.
        for left in range(16):
            for right in range(16):
                shadow = bytearray(8000)
                for x,color in enumerate((left,right)):
                    for plane,bit in enumerate((4,2,1,8)):
                        if color&bit: shadow[plane*20] |= 128>>x
                vram = bytearray([0xa5]*16384)
                self.assertEqual(M.present(shadow,vram,(0,0,2,1)),8)
                self.assertEqual(vram[:2],bytes((0xde,(left<<4)|right)))
                self.assertEqual(vram[8:],bytes([0xa5])*(16384-8))
        offsets = {M.attribute_offset(x,y) for y in range(100) for x in range(160)}
        self.assertEqual(offsets,set(range(1,16000,2)))

    def test_full_capture_and_clipped_immediate_updates(self):
        rng = random.Random(160100)
        shadow = bytearray(rng.randrange(256) for _ in range(8000))
        vram = bytearray([0x69]*16384)
        self.assertEqual(M.present(shadow,vram,(-300,-300,999,999)),16000)
        pixels = M.decode(vram)
        for y in range(100):
            for x in range(160): self.assertEqual(pixels[y][x],M.shadow_pixel(shadow,x,y))
        self.assertEqual(vram[16000:],bytes([0x69])*384)
        for rect in ((159,99,160,100),(1,1,2,2),(-8,3,1,4),(80,80,10,10),(160,100,200,200)):
            before = bytes(vram)
            shadow[0] ^= 0xff
            M.present(shadow,vram,rect)
            x0,y0,x1,y1 = rect
            allowed = set()
            if max(0,x0)<min(160,x1) and max(0,y0)<min(100,y1):
                for y in range(max(0,y0),min(100,y1)):
                    for x in range(max(0,x0)//8*8,(min(160,x1)+7)//8*8,2):
                        off=M.attribute_offset(x,y);allowed.update((off-1,off))
            self.assertTrue(all(a==b or i in allowed for i,(a,b) in enumerate(zip(before,vram))))
        vram[15998] = 0
        with self.assertRaises(ValueError): M.decode(vram)

    def test_cursor_all_edges_and_saved_limit(self):
        maximum=0
        for x in range(-32,161):
            for y in (-32,-1,0,1,68,69,99,100):
                offsets=M.cursor_rectangle(x,y,32,32)
                maximum=max(maximum,len(offsets))
                self.assertTrue(all(0 <= off < 16000 for off in offsets))
                self.assertEqual(len(offsets),len(set(offsets)))
                # Save whole pairs so each unaffected neighbour is restored.
                saved=set(offsets)
                self.assertTrue(all(off^1 in saved for off in offsets))
        self.assertEqual(maximum,1088)

    def test_primary_timing_and_enable_fragment(self):
        source=re.sub(r';[^\n]*','',S.read(HERE/'CGA100E.ASM'))
        registers={}
        for value in re.findall(r'mov ax,([0-9a-f]+)h\s*\n\s*out dx,ax',source,re.I):
            word=int(value,16);registers[word&255]=word>>8
        self.assertEqual(tuple(registers[i] for i in range(16)),
                         (0x71,0x50,0x5a,0x0a,0x7f,6,0x64,0x70,2,1,0x20,0,0,0,0,0))
        self.assertEqual((registers[4]+1)*(registers[9]+1)+registers[5],262)
        self.assertEqual(registers[7]*(registers[9]+1),224)
        self.assertEqual(registers[6]*(registers[9]+1),200)


def font_checks(out):
    rec=F.build(out)
    # Use the existing independent FNT/NE contract validator unchanged.
    sys.modules['BUILD']=F.B
    inspect=importlib.machinery.SourceFileLoader('INSPECT',str(F.KIT/'INSPECT.PY')).load_module()
    validator=importlib.machinery.SourceFileLoader('cga_font_validator',str(F.KIT/'TEST.PY')).load_module()
    for name,item in rec['fonts'].items():
        data=(out/name).read_bytes()
        module,entries=inspect.resources(data)
        font_entry=next(e for e in entries if e[0]==0x8008)
        off=font_entry[3]
        raw=data[off:off+struct.unpack_from('<I',data,off+2)[0]]
        info=validator.validate_fnt(raw)
        expected = (6,5,4,48,40) if name.startswith('CG2') else (5,5,3,48,40) if name in ('CG1SYS.FON','CG1HELV.FON') else (5,5,4,48,40) if name=='CG1COUR.FON' else (6,5,4,48,40)
        assert (info['height'],info['ascent'],info['avg_width'],info['horiz_res'],info['vert_res'])==expected
        validator.validate_fon(data,{'module':module,'resources':[{'id':item['rid'],'font':info}]})
        assert not any(code in item['fallback_bytes'] for code in range(32,127))
    # Common ambiguous characters must stay distinct in the actual drawings.
    for chars in ('0O8','Il1','B68','rn','mw','ce'):
        assert len({tuple(F.G[ch]) for ch in chars})==len(chars),chars
        assert len({tuple(tuple(row) for row in F.drawing(ch,F.ui_width(ch),5)) for ch in chars})==len(chars),chars
    # Actual stock File Open static-control widths observed natively.
    for text,width in (('Filename:',26),('Directory:',26),('Find What:',34)):
        assert sum(F.ui_width(ch) for ch in text)<=width,(text,width)
    for text,width in (('Filename:',35),('Directory:',35)):
        assert sum(F.medium_width(ch) for ch in text)<=width,(text,width)
    F.specimen(out)
    return {n:rec['fonts'][n]['sha256'] for n in rec['fonts']}


def inventory_checks():
    inf=S.read(HERE/'OEMSETUP.INF')
    choices=re.findall(r'^(cga\d+) = a:([^,]+),"([^"]+)","([^"]+)"',inf,re.M)
    assert len(choices)==3
    assert {v[1] for v in choices}=={v[1] for v in S.MODES.values()}
    assert all(len(v[2])<=47 for v in choices)
    assert choices[0][3]=='100,48,40'
    for name in list(F.FACES)+[v[1] for v in choices]:
        p=Path(name)
        assert len(p.stem)<=8 and len(p.suffix)==4 and name==name.upper()
    # Source-file byte policy, including fragments fed to MASM.
    for path in HERE.iterdir():
        if path.is_file():
            raw=path.read_bytes()
            assert b'\n' not in raw.replace(b'\r\n',b''),'CRLF: '+path.name
    return {'oem_choices':len(choices),'descriptor':'SOURCE_CANDIDATE_ONLY','crlf':'PASS'}


def stage_checks(repo,out):
    result={}
    for mode in S.MODES:
        directory=out/mode
        directory.mkdir()
        report=S.stage(repo,directory,mode)
        renderer=directory/'renderer'
        soft=S.read(renderer/'EGA/TSOFT.ASM')
        if mode=='160x100x16':
            cur=S.read(renderer/'EGA/TCURSOR.ASM')
            assert 'SCREEN_HEIGHT equ 100' in soft and 'shadow_bits db 8000 dup' in soft
            assert 'mov ax,0008h' not in soft and 'and ax,1\n    mov cl,13' not in soft
            assert soft.count('mov byte ptr es:[di],0deh')==4
            assert soft.count('call cga_vram_begin')==soft.count('call cga_vram_end')==4
            assert cur.count('call cga_vram_begin')==cur.count('call cga_vram_end')==2
            assert 'db 1088 dup' in cur and not re.search(r'cmp (?:ax|bx|tc_bottom),200',cur)
            assert 'mov dx,160' in cur and 'mov dx,80' not in cur
            for name in ('MIN.BMP','MAX.BMP','RESTORE.BMP','UP.BMP','DOWN.BMP'):
                raw=(directory/'resources'/name).read_bytes()
                assert struct.unpack_from('<H',raw,20)[0]==6
            assert struct.unpack_from('<HH',(directory/'resources/OBUTTON.BMP').read_bytes(),18)==(24,18)
            fonts=S.read(directory/'resources/FONTS.ASM')
            assert 'AnsiVar \tdw\t5\t\t;lfheight\n\t\tdw\t3\t\t;lfwidth' in fonts
            assert 'AnsiFixed\tdw\t6' in fonts and 'OEMFixed\tdw\t6' in fonts
        else:
            # Independently invoke the baseline pipeline, proving that the
            # CGA names introduce no changes to the normal-mode source set.
            baseline=out/('baseline-'+mode);baseline.mkdir()
            br,bs,_=S.pipeline(repo,baseline,mode)
            for root,other in ((renderer,br),(directory/'resources',bs)):
                for path in root.rglob('*'):
                    if path.is_file(): assert path.read_bytes()==(other/path.relative_to(root)).read_bytes(),path
        result[mode]={'host_stage':'PASS','files':len(report['staged_sha256']),
                      'tsoft_sha256':hashlib.sha256((renderer/'EGA/TSOFT.ASM').read_bytes()).hexdigest(),
                      'native':'NOT_TESTED'}
    return result


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repo',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args()
    if args.out.exists(): raise SystemExit('Choose a fresh --out')
    args.out.mkdir(parents=True)
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(Memory)
    checked=unittest.TextTestRunner(verbosity=2).run(suite)
    if not checked.wasSuccessful(): raise SystemExit(1)
    report=dict(host='PASS',native_build='NOT_RUN',windows='NOT_RUN',hardware='UNQUALIFIED',
                memory_cases=checked.testsRun,fonts=font_checks(args.out/'fonts'),
                stages=stage_checks(args.repo.resolve(),args.out),inventory=inventory_checks())
    S.write(args.out/'CGAHOST.JSN',json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__': main()
