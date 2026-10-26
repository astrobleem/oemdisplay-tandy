from pathlib import Path
import re, struct
from capstone import Cs, CS_ARCH_X86, CS_MODE_16
from capstone.x86_const import X86_OP_IMM, X86_OP_MEM, X86_OP_REG, X86_REG_CS, X86_REG_DS, X86_REG_ES

DATA_NAMES = ('dec_q_head','dec_q_tail','dec_q_count','dec_lost_word',
              'timestamp_table','timestamp_oldhead')

def map_symbols(text):
    result={}
    for line in text.splitlines():
        m=re.match(r'^\s*([0-9A-Fa-f]{4}):([0-9A-Fa-f]{4})\*?\s+(\w+)\s*$',line)
        if m:
            result[m.group(3)]=int(m.group(2),16)
    return result

def decode_region(blob,start,size,base=0):
    md=Cs(CS_ARCH_X86,CS_MODE_16); md.detail=True
    return list(md.disasm(blob[start:start+size],base+start))

def check_insns(insns,offsets,scope):
    rows=[]; hits={name:0 for name in offsets}
    byoff={offset:name for name,offset in offsets.items()}
    table_base=offsets['timestamp_table']
    for ins in insns:
        for op in ins.operands:
            if op.type!=X86_OP_MEM: continue
            name=byoff.get(op.mem.disp)
            table_delta=None
            if table_base <= op.mem.disp < table_base+128 and op.mem.segment in (0,X86_REG_DS,X86_REG_CS):
                name='timestamp_table'; table_delta=op.mem.disp-table_base
            if not name: continue
            if op.mem.segment==X86_REG_CS:
                raise AssertionError(f'{scope} has CS data operand at {ins.address:04x}: {ins.bytes.hex()} {ins.mnemonic} {ins.op_str}')
            if op.mem.segment not in (0,X86_REG_DS):
                raise AssertionError(f'{scope} has unexpected segment on {ins.address:04x}: {ins.op_str}, seg={op.mem.segment}')
            hits[name]+=1
            rows.append({'offset':f'{ins.address:04x}','bytes':ins.bytes.hex(),
                         'asm':f'{ins.mnemonic} {ins.op_str}', 'symbol':name,
                         'segment':'DS-explicit' if op.mem.segment==X86_REG_DS else 'DS-default',
                         'table_displacement':None if table_delta is None else f'{table_delta:02x}'})
    return rows,hits

def cs_negative_controls(offsets):
    from types import SimpleNamespace as NS
    exercised=[]
    for delta in (0,2):
        op=NS(type=X86_OP_MEM,mem=NS(segment=X86_REG_CS,disp=offsets['timestamp_table']+delta,
                                    base=0,index=0,scale=1))
        ins=NS(address=0xffff,bytes=b'\x2e',mnemonic='mov',op_str='cs:[bx+table+%d]'%delta,
               operands=[op])
        try:
            check_insns([ins],offsets,'CS negative control')
        except AssertionError as exc:
            assert 'CS data operand' in str(exc),str(exc)
            exercised.append(delta)
        else:
            raise AssertionError('CS table operand at +%d escaped linked-data guard'%delta)
    return {'status':'PASS','rejected_CS_table_offsets':[f'{x:02x}' for x in exercised]}

def verify_ne(root):
    image=(root/'WHEEL.DRV').read_bytes(); maptxt=(root/'WHEEL.MAP').read_text(errors='replace')
    symbols=map_symbols(maptxt)
    offsets={n:symbols[n] for n in DATA_NAMES}
    ne=struct.unpack_from('<I',image,0x3c)[0]
    word=lambda o:struct.unpack_from('<H',image,ne+o)[0]
    shift=word(0x32); sector,size,flags,minimum=struct.unpack_from('<4H',image,ne+word(0x22))
    codeoff=sector<<shift; codelen=size or 65536
    code=image[codeoff:codeoff+codelen]
    instr=decode_region(code,0,len(code))
    # Current driver IRQ4 starts at 0232; public API 13 begins at the verified MAP symbol.
    api=symbols['WheelReadDeltaAge']
    relevant=[i for i in instr if 0x0232<=i.address<api or api<=i.address<codelen]
    controls=cs_negative_controls(offsets)
    rows,hits=check_insns(relevant,offsets,'linked NE')
    needed=('dec_q_head','dec_q_tail','dec_q_count','timestamp_table','timestamp_oldhead')
    assert all(hits[n]>0 for n in needed), hits
    assert any(r['symbol']=='timestamp_table' and r['table_displacement']=='00' for r in rows)
    assert any(r['symbol']=='timestamp_table' and r['table_displacement']=='02' for r in rows)
    assert flags&0x40 and not flags&0x10 and not flags&0x1000
    return {'status':'PASS','code_file_offset':codeoff,'code_length':codelen,
            'dgroup_offsets':{k:f'{v:04x}' for k,v in offsets.items()},
            'references':rows,'reference_counts':hits,'cs_negative_controls':controls}

def verify_dos(root):
    image=(root/'DTEST.EXE').read_bytes(); maptxt=(root/'DTEST.MAP').read_text(errors='replace')
    symbols=map_symbols(maptxt)
    # Map addresses for DGROUP symbols are segment:offset; only the DGROUP offset matters with DS loaded.
    offsets={n:symbols[n] for n in DATA_NAMES}
    header_paras=struct.unpack_from('<H',image,8)[0]; loadoff=header_paras*16
    textm=re.search(r'^_TEXT\s+CODE\s+AUTO\s+[0-9A-Fa-f]{4}:([0-9A-Fa-f]{4})\s+([0-9A-Fa-f]{8})',maptxt,re.M)
    assert textm and int(textm.group(1),16)==0
    textlen=int(textm.group(2),16)
    code=image[loadoff:loadoff+textlen]
    instr=decode_region(code,0,len(code))
    controls=cs_negative_controls(offsets)
    rows,hits=check_insns(instr,offsets,'linked DOS harness')
    assert all(hits[n]>0 for n in DATA_NAMES), hits
    # Generated test fixture code starts at HarnessMain; assert its table writes are also DS/default.
    harness=symbols['HarnessMain']
    fixtures=[i for i in instr if i.address>=harness]
    fixture_rows,fixture_hits=check_insns(fixtures,offsets,'linked DOS fixture')
    assert fixture_hits['timestamp_table']>0 and fixture_hits['dec_q_count']>0 and fixture_hits['dec_lost_word']>0
    assert any(r['table_displacement']=='7c' for r in fixture_rows) and any(r['table_displacement']=='7e' for r in fixture_rows)
    return {'status':'PASS','load_module_file_offset':loadoff,'text_length':textlen,
            'dgroup_offsets':{k:f'{v:04x}' for k,v in offsets.items()},
            'references':rows,'reference_counts':hits,'cs_negative_controls':controls,
            'fixture_references':fixture_rows,'fixture_reference_counts':fixture_hits}

def group_selector(maptxt):
    m=re.search(r'^DGROUP\s+([0-9A-Fa-f]{4}):',maptxt,re.M)
    assert m
    return int(m.group(1),16)

def ne_code(root):
    image=(root/'WHEEL.DRV').read_bytes(); ne=struct.unpack_from('<I',image,0x3c)[0]
    word=lambda o:struct.unpack_from('<H',image,ne+o)[0]
    shift=word(0x32); sector,size,flags,minimum=struct.unpack_from('<4H',image,ne+word(0x22))
    off=sector<<shift; length=size or 65536
    return image[off:off+length],map_symbols((root/'WHEEL.MAP').read_text(errors='replace'))

def dos_code(root):
    image=(root/'DTEST.EXE').read_bytes(); loadoff=struct.unpack_from('<H',image,8)[0]*16
    maptxt=(root/'DTEST.MAP').read_text(errors='replace')
    m=re.search(r'^_TEXT\s+CODE\s+AUTO\s+[0-9A-Fa-f]{4}:([0-9A-Fa-f]{4})\s+([0-9A-Fa-f]{8})',maptxt,re.M)
    assert m and int(m.group(1),16)==0
    length=int(m.group(2),16)
    return image[loadoff:loadoff+length],map_symbols(maptxt),group_selector(maptxt),image,maptxt

def require_named_branch_target(ne_reverse,dos_reverse,ne_target,dos_target):
    ne_name=ne_reverse.get(ne_target); dos_name=dos_reverse.get(dos_target)
    assert ne_name is not None and ne_name==dos_name, (ne_target,dos_target,ne_name,dos_name)
    return ne_name

def branch_target_negative_control():
    try:
        require_named_branch_target({}, {}, 0x1234, 0x5678)
    except AssertionError:
        return {'status':'PASS','rejected_unequal_unmapped_targets':['1234','5678']}
    raise AssertionError('unequal unmapped branch targets escaped procedure checker')

def verify_driver_procedure_correspondence(root):
    nebytes,nemap=ne_code(root); dosbytes,dosmap,dos_group,dosimage,dosmaptxt=dos_code(root)
    harness=dosmap['HarnessMain']
    assert harness==nemap['dec_reset'], (harness,nemap['dec_reset'])
    md=Cs(CS_ARCH_X86,CS_MODE_16); md.detail=True
    nins=list(md.disasm(nebytes[:harness],0)); dins=list(md.disasm(dosbytes[:harness],0))
    assert len(nins)==len(dins) and [(i.address,i.size) for i in nins]==[(i.address,i.size) for i in dins]
    assert nins[-1].address+nins[-1].size==harness
    nreverse={v:k for k,v in nemap.items()}; dreverse={v:k for k,v in dosmap.items()}
    reloc_offsets=set()
    ne=(root/'WHEEL.DRV').read_bytes(); nehead=struct.unpack_from('<I',ne,0x3c)[0]
    nw=lambda o:struct.unpack_from('<H',ne,nehead+o)[0]
    shift=nw(0x32); sec=struct.unpack_from('<4H',ne,nehead+nw(0x22)); codeoff=sec[0]<<shift; codelen=sec[1] or 65536
    code=ne[codeoff:codeoff+codelen]
    if sec[2]&0x100:
        rp=codeoff+codelen; cnt=struct.unpack_from('<H',ne,rp)[0]
        for j in range(cnt):
            _,_,off,_,_=struct.unpack_from('<BBHHH',ne,rp+2+j*8); reloc_offsets.add(off)
    rel_count=struct.unpack_from('<H',dosimage,6)[0]; rel_table=struct.unpack_from('<H',dosimage,0x18)[0]
    dos_relocs=set()
    for j in range(rel_count):
        off,seg=struct.unpack_from('<HH',dosimage,rel_table+j*4); dos_relocs.add(seg*16+off)
    assert any(x in (0x23d,0x23e) for x in reloc_offsets), sorted(reloc_offsets)
    assert any(x in (0x23d,0x23e) for x in dos_relocs), sorted(dos_relocs)

    def memory_match(a,b,ma,mb):
        x,y=a.mem.disp,b.mem.disp
        if (a.mem.base,a.mem.index,a.mem.scale)!=(b.mem.base,b.mem.index,b.mem.scale): return False
        # CS references to the driver's code-segment state are intentionally
        # retained in both builds. Linked-data checks above separately reject
        # CS operands whose offsets resolve to DGROUP symbols/table slots.
        if a.mem.segment==X86_REG_CS or b.mem.segment==X86_REG_CS:
            return a.mem.segment==b.mem.segment and x==y
        if a.mem.segment not in (0,X86_REG_DS) or b.mem.segment not in (0,X86_REG_DS):
            return a.mem.segment==b.mem.segment and x==y
        if x==y: return True
        # External names carry their respective linker-assigned DGROUP offsets.
        for name,nval in ma.items():
            if nval==x and mb.get(name)==y: return True
        # Ring accesses are base plus table offset; maintain the same in-table displacement.
        nt=ma.get('timestamp_table'); dt=mb.get('timestamp_table')
        if nt is not None and dt is not None and nt<=x<nt+128 and dt<=y<dt+128:
            return x-nt==y-dt
        # The test-only fixture bytes follow the driver's original data; this linker
        # places DOS DGROUP at offset 4 versus NE DGROUP at offset 0.
        if 0<=x<0x12 and y==x+4: return True
        return False

    diffs=[]
    for a,b in zip(nins,dins):
        assert a.address==b.address and a.mnemonic==b.mnemonic and len(a.operands)==len(b.operands), (a.address,a,b)
        for oi,(x,y) in enumerate(zip(a.operands,b.operands)):
            assert x.type==y.type, (a.address,oi,x.type,y.type)
            if x.type==X86_OP_REG:
                assert x.reg==y.reg, (a.address,oi,a,b)
            elif x.type==X86_OP_MEM:
                assert x.size==y.size and memory_match(x,y,nemap,dosmap), (a.address,oi,a,b)
                if x.mem.disp!=y.mem.disp: diffs.append({'address':f'{a.address:04x}','kind':'DGROUP memory displacement','ne':f'{x.mem.disp:04x}','dos':f'{y.mem.disp:04x}'})
            elif x.type==X86_OP_IMM:
                if x.imm==y.imm: continue
                if a.mnemonic in ('call','jmp','ja','jae','jb','jbe','je','jne','jg','jge','jl','jle','jo','jno','js','jns','jp','jnp','loop','loope','loopne'):
                    symbol=require_named_branch_target(nreverse,dreverse,x.imm,y.imm)
                    diffs.append({'address':f'{a.address:04x}','kind':'linked code target','symbol':symbol})
                elif a.address==0x23c and x.imm==0xffff and y.imm==dos_group:
                    diffs.append({'address':f'{a.address:04x}','kind':'DGROUP selector relocation','dos_selector':f'{y.imm:04x}'})
                else: raise AssertionError((a.address,oi,a,b))
    return {'status':'PASS','compared_code_range':f'0000:{harness:04x}',
            'instruction_count':len(nins),'normalized_linker_differences':diffs,
            'branch_target_negative_control':branch_target_negative_control(),
            'candidate_api_offset':f'{nemap["WheelReadDeltaAge"]:04x}',
            'harness_entry_offset':f'{harness:04x}'}

if __name__=='__main__':
    import json,sys
    root=Path(__file__).resolve().parent
    print(json.dumps({'ne':verify_ne(root),'dos':verify_dos(root),
                      'procedure_correspondence':verify_driver_procedure_correspondence(root)},indent=2))

