#!/usr/bin/env python3
"""Static scope, pin and fail-closed staging checks; no runtime claims."""
from pathlib import Path
import argparse, hashlib, importlib.machinery, json, tempfile

MODES={'320x200x16':'build32016','640x200x4':'build6404','160x200x16':'build16016','320x200x4':'build3204','640x200x2':'build6402'}
EXT={'.ASM','.INC','.BLT','.PUB','.MAC','.DEF','.LNK','.RC','.BAT'}
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--baseline',type=Path,required=True);p.add_argument('--combined',action='store_true');a=p.parse_args()
 mod=importlib.machinery.SourceFileLoader('curkeep',str(a.root/'src/tandysw/CURKEEP.PY')).load_module()
 n=mod.normalized
 report={'status':'PASS','scope':'static staging and assembly checks only','builds':[],'fail_closed_tests':[]}
 inherited=[]
 for rel in ['src/tandysw/V1.ASM','src/tandysw/TCURSOR.ASM','src/tandysw/PORT8086.PY','src/tandysw/PORTDIB.PY','src/tandysw/MODEPROF.PY','src/tandysw/REPCOPY88.PY','src/tandysw/AUDIT88.PY','src/tandysw/build.py']+(['src/tandysw/BYTECOL.PY'] if a.combined else []):
  assert (a.root/rel).read_bytes()==(a.baseline/rel).read_bytes(),rel
  inherited.append({'file':rel,'sha256':digest(a.root/rel)})
 report['unchanged_upstream_inputs']=inherited
 for mode,build in MODES.items():
  old=a.baseline/build;new=a.root/build
  srcold=old/'renderer/EGA';srcnew=new/'renderer/EGA'
  d=json.loads((new/'RESULT.json').read_text())
  assert not d['instruction_audit']['unsupported'];assert not d['rep_prefix_audit']['multi_prefix_rep']
  bd=json.loads((old/'RESULT.json').read_text())
  assert d['rep_prefix_audit']['replacement_sites']==bd['rep_prefix_audit']['replacement_sites']
  assert digest(new/'resources/TANDY.RES')==digest(old/'resources/TANDY.RES')
  changes=[]
  for op in (old/'renderer').rglob('*'):
   if op.is_file() and op.suffix.upper() in EXT:
    rel=op.relative_to(old/'renderer'); np=new/'renderer'/rel
    assert np.exists(),str(rel)
    if op.read_bytes()!=np.read_bytes():changes.append(str(rel))
  assert sorted(changes)==['EGA/TCURSOR.ASM','EGA/TSOFT.ASM'],changes
  objs=[]
  for op in srcold.glob('*.OBJ'):
   if op.name not in ('TSOFT.OBJ','TCURSOR.OBJ'):
    assert op.read_bytes()==(srcnew/op.name).read_bytes(),op.name
    objs.append({'file':op.name,'sha256':digest(op)})
  before=n(srcold/'TSOFT.ASM');after=n(srcnew/'TSOFT.ASM')
  stride=int(mode.split('x')[0])//8*mod.PHYSICAL_BYTES[mode]
  rows=mod.rows_helper(before,stride); cols=mod.columns_helper(before,mod.PHYSICAL_BYTES[mode]) if a.combined else ''
  inverse=mod.once(after,'FlushShadow endp\n'+rows+cols,'FlushShadow endp\n')
  inverse=mod.once(inverse,'externFP cursor_show\nexternFP cursor_begin_retain\nexternFP cursor_end_retain\nexternFP cursor_invalidate\n','externFP cursor_show\n')
  b,e=inverse.index('cProc TBitBlt,'),inverse.index('cProc TOutput,');blt=inverse[b:e]
  blt=mod.once(blt,'    call FlushRetainRows\n','    call FlushRows\n')
  if a.combined:blt=mod.once(blt,'    call FlushRetainColumns\n','    call FlushColumns\n')
  inverse=inverse[:b]+blt+inverse[e:]
  b,e=inverse.index('cProc TPixel,'),inverse.index('cProc TScanLR,');pix=inverse[b:e]
  legacy='FlushColumns' if a.combined else 'FlushRows';retain='FlushRetainColumns' if a.combined else 'FlushRetainRows'
  pix=mod.once(pix,'    call '+retain+'\n    jmp short TPixel_flushed\nTPixel_flush:\n    call '+legacy+'\nTPixel_flushed:\n','TPixel_flush:\n    call '+legacy+'\n')
  inverse=inverse[:b]+pix+inverse[e:]
  inverse=mod.once(inverse,'    cmp enabled_flag,0\n    jne enable_ok\n    call cursor_invalidate\n','    cmp enabled_flag,0\n    jne enable_ok\n')
  inverse=mod.once(inverse,'    pushf\n    cli\n    mov enabled_flag,0\n    call cursor_invalidate\n    popf\n    mov al,old_mode\n','    mov enabled_flag,0\n    mov al,old_mode\n')
  assert inverse==before,'Unapproved TSOFT delta '+mode
  cur_before=n(srcold/'TCURSOR.ASM');cur_after=n(srcnew/'TCURSOR.ASM')
  assert mod.once(cur_after,'cursor_show endp\n'+mod.cursor_helpers(stride),'cursor_show endp\n')==cur_before
  # Every original public body and private hide/show/refresh/draw/erase stays exact.
  assert cur_after.split('cProc Inquire,',1)[1]==cur_before.split('cProc Inquire,',1)[1]
  with tempfile.TemporaryDirectory(prefix='curkeep-') as td:
   stage=Path(td)/'EGA';stage.mkdir()
   originals={f:(srcold/f).read_bytes() for f in ('TSOFT.ASM','TCURSOR.ASM')}
   # Both independent source pins reject even a harmless comment-byte mutation,
   # before either destination changes. Unsupported profile/variant also fail.
   for bad in ('TSOFT.ASM','TCURSOR.ASM'):
    for f,data in originals.items():(stage/f).write_bytes(data+(b'; altered input\r\n' if f==bad else b''))
    snap={f:(stage/f).read_bytes() for f in originals}
    try:mod.port(stage.parent,mode,a.combined)
    except RuntimeError:pass
    else:raise AssertionError('Accepted altered input '+bad)
    assert all((stage/f).read_bytes()==data for f,data in snap.items())
    report['fail_closed_tests'].append({'mode':mode,'mutated_input':bad,'result':'REJECTED_WITHOUT_WRITES'})
   for f,data in originals.items():(stage/f).write_bytes(data)
   mod.port(stage.parent,mode,a.combined)
   assert all((stage/f).read_bytes()==(srcnew/f).read_bytes() for f in originals),'Reproduction mismatch'
  for f in ('TSOFT.ASM','TCURSOR.ASM'):
   data=(srcnew/f).read_bytes();assert b'\n' not in data.replace(b'\r\n',b''),'Non-CRLF'
  driver=next(new.glob('*.DRV'))
  report['builds'].append({'mode':mode,'driver':str(driver.relative_to(a.root)),'driver_bytes':driver.stat().st_size,'driver_sha256':digest(driver),'baseline_sha256':digest(next(old.glob('*.DRV'))),'growth_bytes':driver.stat().st_size-next(old.glob('*.DRV')).stat().st_size,'build':'PASS','isa':'PASS','multi_prefix_rep_count':0,'safe_copy_sites':'BYTE_IDENTICAL','resource_sha256':digest(new/'resources/TANDY.RES'),'changed_staged_sources':changes,'unchanged_objects':objs,'staged_raw_sha256':{f:digest(srcnew/f) for f in ('TSOFT.ASM','TCURSOR.ASM')},'staged_normalized_sha256':{f:mod.sha(n(srcnew/f)) for f in ('TSOFT.ASM','TCURSOR.ASM')},'scope_inverse':'EXACT_BASELINE','public_cursor_apis':'SOURCE_IDENTICAL','legacy_flush_helpers':'SOURCE_IDENTICAL','mode_transition_changes':'ONLY_DISABLED_HARDWARE_ENABLE_AND_DISABLE'})
 report['source_sha256']={f:digest(a.root/'src/tandysw'/f) for f in ('BUILD88.PY','CURKEEP.PY','VERKEEP.PY')}
 report['token_states']={'0':'legacy hide acquired','1':'retained owned depth','2':'consumed; repeated end no-op','other':'invalid; no depth release; becomes consumed'}
 report['runtime']='INDEPENDENT_TESTS_REQUIRED';report['native_benefit']='NOT_MEASURED';report['physical_acceptance']='NOT_RUN';report['installed_or_published']=False
 (a.root/'BUILDS.JSN').write_bytes((json.dumps(report,indent=2)+'\n').replace('\n','\r\n').encode())
 print(json.dumps({'status':report['status'],'builds':len(report['builds']),'fail_closed_tests':len(report['fail_closed_tests']),'report':str(a.root/'BUILDS.JSN')},indent=2))
if __name__=='__main__':main()
