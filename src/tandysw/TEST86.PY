#!/usr/bin/env python3
"""Reproducible semantic tests for the staged DDK 8088 port, under DOSBox-X.

Exercises the actual port's save-frame expansions and runtime rotate-generator
source. A successful result is instruction-semantic evidence, not a Windows GUI
or real-hardware validation. Run in a fresh output directory:
  python TEST86.PY --dosbox /path/to/dosbox-x --out /tmp/test86
"""
from pathlib import Path
import argparse
import importlib.machinery
import importlib.util
import json
import os
import re
import subprocess
import build as baseline

HERE = Path(__file__).resolve().parent


def save_source(m):
    flags=[sum(bit for bit,mask in zip([1,4,16,64,128,1024,2048],[1,2,4,8,16,32,64]) if n&mask)|0x202 for n in range(128)]
    regs=[('ax',0x1111),('cx',0x2222),('dx',0x3333),('bx',0x4444),('bp',0x5555),('si',0x6666),('di',0x7777)]
    head='''.8086
    code segment para public 'CODE'
    assume cs:code,ds:code,ss:stackseg
    check macro a,b
     local okay
     cmp a,b
     je okay
     jmp failed
    okay:
    endm
    start:
     mov ax,code
     mov ds,ax
     mov word ptr test_index,0
    next_test:
     mov bx,test_index
     mov ax,flag_table[bx]
     push ax
     popf
     pushf
     pop expected_flags
     mov expected_sp,sp
    '''
    body=''.join(f' mov {r},{v:05x}h\n' for r,v in regs)
    body+=' '+m.PUSHA86+'\n pushf\n pop actual_flags\n'
    body+=''.join(f' check {r},{v:05x}h\n' for r,v in regs)
    body+=' mov bp,sp\n'
    for i,(r,v) in enumerate(reversed(regs)):
     off=i*2 if i<3 else (i+1)*2
     body+=f' check <word ptr ss:[bp+{off}]>,{v:05x}h\n'
    body+=' mov ax,expected_sp\n check ss:[bp+6],ax\n mov ax,expected_flags\n check actual_flags,ax\n'
    body+=' push expected_flags\n popf\n '+m.POPA86+'\n pushf\n pop actual_flags\n'
    body+=''.join(f' check {r},{v:05x}h\n' for r,v in regs)
    body+=' mov ax,expected_sp\n check sp,ax\n mov ax,expected_flags\n check actual_flags,ax\n'
    body+=' add test_index,2\n cmp test_index,256\n je tests_done\n jmp next_test\ntests_done:\n cld\n mov dx,offset passed\n mov ah,9\n int 21h\n mov ax,4c00h\n int 21h\nfailed:\n cld\n mov dx,offset failure\n mov ah,9\n int 21h\n mov ax,4c01h\n int 21h\n'
    data="passed db 'PASS: 128 flag patterns; full PUSHA frame, registers, SP and POPA flags',13,10,'$'\nfailure db 'FAIL',13,10,'$'\nexpected_flags dw ?\nactual_flags dw ?\nexpected_sp dw ?\ntest_index dw ?\nflag_table dw "+'\n dw '.join(','.join(f'{v:05x}h' for v in flags[i:i+8]) for i in range(0,128,8))+'\ncode ends\nstackseg segment para stack\n dw 512 dup (?)\nstackseg ends\nend start\n'
    return head + body + data


def rotate_source(r):
    cblt=(r/'CBLT.ASM').read_text()
    a=cblt.index('\tmov\tcl,dh',cblt.index('cblt_3240:'))
    b=cblt.index('; Do not generate phase masking',a)
    snippet=cblt[a:b].replace('\terrnz\t<', '\t.errnz\t').replace('I_ROR_AL_1)>', 'I_ROR_AL_1)')
    s='''.8086
    code segment para public 'CODE'
    assume cs:code,ds:code
    I_ROL_AL_1 equ 0c0d0h
    I_ROR_AL_1 equ 0c8d0h
    check macro a,b
     local okay
     cmp a,b
     je okay
     jmp failed
    okay:
    endm
    start:
     mov ax,code
     mov ds,ax
     mov es,ax
     mov phase,0
    next_phase:
     cld
     xor cx,cx
     mov di,offset buffer
     mov dh,phase
     or dh,dh
     jz finish_gen
    '''+snippet+'''finish_gen:
     mov al,0c3h
     stosb
     mov value,0
    next_value:
     mov caseflags,00202h
    next_flags:
     mov cl,phase
     mov flags_mask,0cd5h
     cmp cl,2
     jb mask_done
     cmp cl,7
     je mask_done
     mov flags_mask,004d5h
    mask_done:
     cmp cl,5
     jb reference_left
     neg cl
     add cl,8
     mov ax,value
     mov ah,0a5h
     push caseflags
     popf
     ror al,cl
     jmp short save_reference
    reference_left:
     mov ax,value
     mov ah,0a5h
     push caseflags
     popf
     rol al,cl
    save_reference:
     mov expected,ax
     pushf
     pop expected_flags
     mov ax,value
     mov ah,0a5h
     mov cx,55aah
     push caseflags
     popf
     call buffer
     pushf
     pop actual_flags
     check ax,expected
     check cx,055aah
     mov ax,actual_flags
     xor ax,expected_flags
     and ax,flags_mask
     check ax,0
     cmp caseflags,00202h
     jne flags_done
     mov caseflags,00ed7h
     jmp next_flags
    flags_done:
     inc value
     cmp value,256
     je value_done
     jmp next_value
    value_done:
     inc phase
     cmp phase,8
     je all_done
     jmp next_phase
    all_done:
     cld
     mov dx,offset passed
     mov ah,9
     int 21h
     mov ax,4c00h
     int 21h
    failed:
     cld
     mov dx,offset failure
     mov ah,9
     int 21h
     mov ax,4c01h
     int 21h
    passed db 'PASS: 4096 generated-code rotation executions, AL/AH, CX and defined FLAGS',13,10,'$'
    failure db 'FAIL',13,10,'$'
    phase db 0
    value dw 0
    caseflags dw ?
    expected dw ?
    expected_flags dw ?
    actual_flags dw ?
    flags_mask dw ?
    buffer label near
     db 16 dup (0)
    code ends
    stackseg segment para stack
     dw 512 dup (?)
    stackseg ends
    end start
    '''
    return s

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=HERE.parents[1])
    parser.add_argument('--dosbox', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    repo, out = args.repo.resolve(), args.out.resolve()
    if out.exists():
        raise SystemExit('Choose a fresh --out directory')
    out.mkdir(parents=True)
    renderer, _ = baseline.prepare(repo, out)
    loader = importlib.machinery.SourceFileLoader('port86test', str(HERE / 'PORT8086.PY'))
    spec = importlib.util.spec_from_loader('port86test', loader)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    audit = module.port(renderer, repo)
    for name in audit['patched_files']:
        raw = (renderer / name).read_bytes()
        if b'\n' in raw.replace(b'\r\n', b''):
            raise AssertionError('Non-CRLF output: ' + name)
    try:
        module.port(renderer, repo)
    except RuntimeError as error:
        if 'Unaudited 8086 input' not in str(error):
            raise
    else:
        raise AssertionError('Reapplying patches unexpectedly succeeded')
    baseline.write_dos(renderer / 'SEM86.ASM', save_source(module))
    baseline.write_dos(renderer / 'ROT86.ASM', rotate_source(renderer))
    batch = ['@echo off', 'R:', 'cd \\']
    for name in ('SEM86', 'ROT86'):
        batch.extend([
            'C:\\BIN\\MASM ' + name + '.ASM,' + name + '.OBJ,' + name + '.LST; > ' + name + '.BLD',
            'C:\\BIN\\LINK ' + name + '.OBJ,' + name + '.EXE; >> ' + name + '.BLD',
            name + '.EXE > ' + name + '.LOG',
        ])
    batch.append('exit')
    baseline.write_dos(renderer / 'TEST86.BAT', '\n'.join(batch) + '\n')
    cfg = out / 'TEST86.CNF'
    cfg.write_text('[sdl]\nfullscreen=false\noutput=surface\n[dosbox]\nmachine=tandy\nmemsize=16\n'
                   'working directory option=force\nworking directory default=' + str(out) +
                   '\n[cpu]\ncore=normal\ncputype=8086_prefetch\ncycles=fixed 200000\n'
                   '[mixer]\nnosound=true\n[midi]\nmididevice=none\n[autoexec]\n@echo off\n'
                   'mount C "' + str(repo) + '"\nmount R "' + str(renderer) + '"\nR:\n')
    env = os.environ.copy()
    env.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy')
    with (out / 'host.log').open('wb') as log:
        subprocess.run([str(args.dosbox.resolve()), '-nopromptfolder', '-conf', str(cfg),
                        '-c', 'R:', '-c', 'TEST86.BAT'], stdout=log, stderr=subprocess.STDOUT,
                       env=env, timeout=120, check=True)
    results = {}
    for name in ('SEM86', 'ROT86'):
        log = (renderer / (name + '.BLD')).read_text(errors='replace')
        errors = re.findall(r'(\d+)\s+Severe\s+Errors', log)
        if not errors or any(int(n) for n in errors) or re.search(r'fatal error|error L\d+', log, re.I):
            raise AssertionError('Test build failed: ' + name + '\n' + log)
        text = (renderer / (name + '.LOG')).read_text(errors='replace').strip()
        if not text.startswith('PASS:'):
            raise AssertionError('Semantic test failed: ' + name + '\n' + text)
        results[name] = text
    results.update({'cpu': '8086_prefetch (8088 four-byte prefetch queue)',
                    'source_pins': audit['pinned_ddk_inputs'], 'crlf': 'PASS', 'reapply_rejected': 'PASS'})
    (out / 'RESULT.json').write_text(json.dumps(results, indent=2) + '\n')
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
