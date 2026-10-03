#!/usr/bin/env python3
"""Execute the exact V1 FlushShadow in isolated 640K Tandy DOSBox-X boots.

Usage: python TESTFB.PY --dosbox /path/to/dosbox-x --out /tmp/new-testfb
Requires Python 3 and the repository's MASM/LINK4. No Windows install is used.
Correctness boots use cycles=200000; the separate 16-frame benchmark uses
cycles=20000 and the BIOS timer (about 54.9 ms batch granularity). All boots use
8086_prefetch, normal Tandy conventional memory, and no XMS/EMS/UMB.
The EXE owns its maximum DOS arena; unused tail memory covers the video alias.
The guest rejects an unsafe live-segment end or an unexpected DOS MCB before
setting video mode, and verifies that MCB after the conversion and file writes.
Output includes raw VRAM, exact extracted assembly, metadata, reference images,
and a machine-readable report. This proves framebuffer content in emulation,
not real-hardware timing or the full Windows rendering/cursor integration.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import selectors
import shutil
import struct
import subprocess
import time

HERE = Path(__file__).resolve().parent
FIELDS = ('psp block_end live_end code_segment shadow_segment stack_segment '
          'stack_end_offset bios_kb_before bios_kb_after bios_mode bios_columns '
          'bios_page_bytes alias_verified mcb_verified hide_count show_count '
          'hide_ds show_ds saved_sp disabled_verified registers_verified '
          'tick_start_low tick_start_high tick_end_low tick_end_high benchmark_frames').split()
SENTINEL = 0xA5
PALETTE = [(0,0,0),(0,0,170),(0,170,0),(0,170,170),(170,0,0),(170,0,170),
           (170,85,0),(170,170,170),(85,85,85),(85,85,255),(85,255,85),
           (85,255,255),(255,85,85),(255,85,255),(255,255,85),(255,255,255)]


def dos_text(path, text):
    path.write_bytes(text.replace('\r\n', '\n').replace('\n', '\r\n').encode('ascii'))


def extract_source(repo):
    text = (repo / 'src/tandysw/V1.ASM').read_text()
    match = re.search(r'^get_nibble macro\n.*?^FlushShadow endp$', text, re.M | re.S)
    if not match:
        raise RuntimeError('Cannot locate exact get_nibble/FlushShadow source')
    return match.group(0) + '\n'


def source(body):
    # The EXE owns its default maximum DOS block, including 9800h..9BFFh.
    # Only unused tail space overlaps video. Every live segment is checked
    # below 9800h BEFORE setting mode 09h; no MCB or DOS allocation is changed.
    return r""".8086
code segment para public 'CODE'
assume cs:code,ds:code,ss:stackseg
JFAIL macro condition
 local okay
 condition okay
 jmp failed
okay:
endm
CHECK macro a,b
 cmp a,b
 JFAIL je
endm
start:
 mov ax,es
 mov bx,code
 mov ds,bx
 mov psp,ax
 mov code_segment,bx
 mov ax,shadowseg
 mov shadow_segment,ax
 mov ax,stackseg
 mov stack_segment,ax
 mov stack_end_offset,offset stack_end
 mov bx,offset stack_end
 add bx,15
 mov cl,4
 shr bx,cl
 add ax,bx
 mov live_end,ax
 cmp ax,9800h
 JFAIL jbe
 mov ax,psp
 dec ax
 mov es,ax
 CHECK <byte ptr es:[0]>,90
 mov ax,psp
 CHECK es:[1],ax
 add ax,es:[3]
 mov block_end,ax
 CHECK ax,9c00h
 xor si,si
 mov di,offset mcb_before
 mov cx,16
save_mcb:
 mov al,es:[si]
 mov [di],al
 inc si
 inc di
 loop save_mcb
 mov ax,40h
 mov es,ax
 mov ax,es:[13h]
 mov bios_kb_before,ax
 CHECK ax,624
 ; Read the full 32768-byte host-generated shadow, including trailing guard.
 mov dx,offset input_name
 mov ax,3d00h
 int 21h
 JFAIL jnc
 mov bx,ax
 push ds
 mov ax,shadowseg
 mov ds,ax
 xor dx,dx
 mov cx,8000h
 mov ah,3fh
 int 21h
 pop ds
 JFAIL jnc
 CHECK ax,8000h
 mov ah,3eh
 int 21h
 JFAIL jnc
 ; BIOS selects the actual 320x200x16 Tandy mode before any VRAM write.
 mov ax,9
 int 10h
 mov mode_set,1
 mov ax,40h
 mov es,ax
 xor ax,ax
 mov al,es:[49h]
 mov bios_mode,ax
 CHECK ax,9
 mov ax,es:[4ah]
 mov bios_columns,ax
 CHECK ax,40
 mov ax,es:[4ch]
 mov bios_page_bytes,ax
 mov ax,es:[13h]
 mov bios_kb_after,ax
 CHECK ax,624
 mov ax,0b800h
 mov es,ax
 xor di,di
 mov ax,0a5a5h
 mov cx,4000h
 cld
 rep stosw
 ; Disabled entry must leave all 32KB untouched and skip both cursor calls.
 call FlushShadow
 mov ax,0b800h
 mov es,ax
 xor di,di
 mov ax,0a5a5h
 mov cx,4000h
 repe scasw
 JFAIL je
 CHECK hide_count,0
 CHECK show_count,0
 mov disabled_verified,1
 ; Enabled entry must preserve the complete register set and stack pointer.
 mov enabled_flag,1
 mov saved_sp,sp
 mov ax,1111h
 mov bx,2222h
 mov cx,3333h
 mov dx,4444h
 mov si,5555h
 mov di,6666h
 mov bp,7777h
 call FlushShadow
 CHECK ax,1111h
 CHECK bx,2222h
 CHECK cx,3333h
 CHECK dx,4444h
 CHECK si,5555h
 CHECK di,6666h
 CHECK bp,7777h
 mov ax,code
 mov bx,ds
 CHECK ax,bx
 mov bx,es
 CHECK bx,0b800h
 mov ax,sp
 CHECK ax,saved_sp
 CHECK hide_count,1
 CHECK show_count,1
 mov ax,code
 CHECK hide_ds,ax
 CHECK show_ds,ax
 mov registers_verified,1
 ; Optional B command times 16 complete flushes at the requested CPU speed.
 mov ax,psp
 mov es,ax
 cmp byte ptr es:[80h],2
 jb no_benchmark
 cmp byte ptr es:[82h],'B'
 jne no_benchmark
 xor ah,ah
 int 1ah
 mov tick_start_low,dx
 mov tick_start_high,cx
 mov cx,16
bench_frame:
 call FlushShadow
 loop bench_frame
 xor ah,ah
 int 1ah
 mov tick_end_low,dx
 mov tick_end_high,cx
 mov benchmark_frames,16
no_benchmark:
 ; Verify this mode really aliases physical 98000h..9BFFFh (first 16KB).
 push ds
 mov ax,0b800h
 mov ds,ax
 mov ax,9800h
 mov es,ax
 xor si,si
 xor di,di
 mov cx,4000h
 repe cmpsb
 pop ds
 JFAIL je
 mov alias_verified,1
 ; Capture all 32768 bytes through B800h while still in graphics mode.
 mov dx,offset output_name
 mov ax,0b800h
 call dump_segment
 mov dx,offset after_name
 mov ax,shadowseg
 call dump_segment
 mov ax,psp
 dec ax
 mov es,ax
 mov si,offset mcb_before
 xor di,di
 mov cx,16
 repe cmpsb
 JFAIL je
 mov mcb_verified,1
 mov dx,offset meta_name
 xor cx,cx
 mov ah,3ch
 int 21h
 JFAIL jnc
 mov bx,ax
 mov dx,offset metadata
 mov cx,metadata_end-metadata
 mov ah,40h
 int 21h
 JFAIL jnc
 CHECK ax,<metadata_end-metadata>
 mov ah,3eh
 int 21h
 JFAIL jnc
 mov ax,3
 int 10h
 mov dx,offset passed
 mov ah,9
 int 21h
 mov ax,4c00h
 int 21h
failed:
 cmp mode_set,0
 je fail_text
 mov ax,3
 int 10h
fail_text:
 mov dx,offset failure
 mov ah,9
 int 21h
 mov ax,4c01h
 int 21h
; DS:DX filename, AX source segment. Never allocates or releases DOS blocks.
dump_segment proc near
 push ax
 xor cx,cx
 mov ah,3ch
 int 21h
 JFAIL jnc
 mov bx,ax
 pop ax
 push ds
 mov ds,ax
 xor dx,dx
 mov cx,8000h
 mov ah,40h
 int 21h
 pop ds
 JFAIL jnc
 CHECK ax,8000h
 mov ah,3eh
 int 21h
 JFAIL jnc
 ret
dump_segment endp
cursor_hide proc far
 pushf
 inc cs:hide_count
 mov cs:hide_ds,ds
 popf
 retf
cursor_hide endp
cursor_show proc far
 pushf
 inc cs:show_count
 mov cs:show_ds,ds
 popf
 retf
cursor_show endp
""" + body + r"""
enabled_flag db 0
mode_set db 0
input_name db 'SHADOW.BIN',0
output_name db 'VRAM.BIN',0
after_name db 'AFTER.BIN',0
meta_name db 'META.BIN',0
passed db 'PASS: exact FlushShadow completed in mode 09h',13,10,'$'
failure db 'FAIL: unsafe placement, I/O, mode, or register check',13,10,'$'
metadata label byte
psp dw 0
block_end dw 0
live_end dw 0
code_segment dw 0
shadow_segment dw 0
stack_segment dw 0
stack_end_offset dw 0
bios_kb_before dw 0
bios_kb_after dw 0
bios_mode dw 0
bios_columns dw 0
bios_page_bytes dw 0
alias_verified dw 0
mcb_verified dw 0
hide_count dw 0
show_count dw 0
hide_ds dw 0
show_ds dw 0
saved_sp dw 0
disabled_verified dw 0
registers_verified dw 0
tick_start_low dw 0
tick_start_high dw 0
tick_end_low dw 0
tick_end_high dw 0
benchmark_frames dw 0
metadata_end label byte
mcb_before db 16 dup(0)
code ends
shadowseg segment para public 'DATA'
shadow_bits db 32768 dup(0)
shadowseg ends
stackseg segment para stack 'STACK'
 dw 512 dup(0)
stack_end label byte
stackseg ends
end start
"""


def run_dos(dosbox, directory, timeout, cycles=200000):
    dos_text(directory / 'RUN.CONF', f"""[sdl]
fullscreen=false
output=surface
[dosbox]
machine=tandy
allow more than 640kb base memory=false
memsize=1
working directory option=force
working directory default={directory}
[cpu]
core=normal
cputype=8086_prefetch
cycles=fixed {cycles}
[mixer]
nosound=true
[midi]
mididevice=none
[dos]
xms=false
ems=false
umb=false
ver=3.30
[autoexec]
@echo off
mount R "{directory}"
R:
RUN.BAT
""")
    env = dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy')
    process = subprocess.Popen([str(dosbox), '-nopromptfolder', '-conf', str(directory / 'RUN.CONF')],
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ)
    deadline, total = time.monotonic() + timeout, 0
    try:
        with (directory / 'HOST.LOG').open('wb') as log:
            while selector.get_map():
                if time.monotonic() > deadline:
                    raise TimeoutError(f'DOSBox timed out: {directory}')
                for key, _ in selector.select(0.25):
                    data = os.read(key.fileobj.fileno(), 8192)
                    if not data:
                        selector.unregister(key.fileobj)
                        break
                    if total < 65536:
                        log.write(data[:65536-total])
                    total += len(data)
        if process.wait(timeout=2):
            raise RuntimeError('DOSBox returned failure')
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        selector.close()
        process.stdout.close()
    host = (directory / 'HOST.LOG').read_text(errors='replace')
    if '8086 cpu type' not in host or 'is not a valid value' in host:
        raise RuntimeError('Requested 8086_prefetch CPU not accepted; inspect HOST.LOG')
    if total > 65536:
        raise RuntimeError('Emulator exceeded bounded host log; inspect HOST.LOG')


def make_shadow(pattern):
    data = bytearray([0x5A] * 32768)
    if pattern == 'swatches':
        for y in range(200):
            for x in range(320):
                # 16 colour columns and changing rows, with distinctive edges.
                colour = ((x // 20) + (y // 25)) % 16
                if y in (0, 199) or x in (0, 319):
                    colour = (x + y) % 16
                # DDK plane 0=R, 1=G, 2=B, 3=I; Tandy bit 0=B, 2=R.
                for plane, bit in enumerate((2, 1, 0, 3)):
                    offset = y * 160 + plane * 40 + x // 8
                    mask = 0x80 >> (x % 8)
                    data[offset] &= ~mask
                    if colour & (1 << bit):
                        data[offset] |= mask
    else:
        state = 0x5EED1234
        for plane in range(4):
            for i in range(8000):
                state ^= (state << 13) & 0xFFFFFFFF
                state ^= state >> 17
                state ^= (state << 5) & 0xFFFFFFFF
                # Explicit every-byte coverage in every plane, then PRNG data.
                value = i if i < 256 else (state & 255)
                data[(i // 40) * 160 + plane * 40 + i % 40] = value
    return bytes(data)


def pixel(shadow, x, y):
    bit = 1 << (7 - x % 8)
    base = y * 160 + x // 8
    r, g, b, i = (bool(shadow[base + plane * 40] & bit) for plane in range(4))
    return (int(i) << 3) | (int(r) << 2) | (int(g) << 1) | int(b)


def reference(shadow):
    result = bytearray([SENTINEL] * 32768)
    for y in range(200):
        for x in range(0, 320, 2):
            address = (y % 4) * 8192 + (y // 4) * 160 + x // 2
            result[address] = pixel(shadow, x, y) * 16 + pixel(shadow, x + 1, y)
    return bytes(result)



def validate_reference():
    # Explicit single-channel expectations avoid a self-consistent RGB/BGR bug.
    for plane, colour in enumerate((4, 2, 1, 8)):
        shadow = bytearray(32768)
        shadow[plane*40] = 0x80
        assert pixel(shadow, 0, 0) == colour
        assert pixel(shadow, 1, 0) == 0
    shadow = bytearray(32768)
    shadow[0] = 0x80       # x=0 red is the high nibble
    shadow[80] = 0x40      # x=1 blue is the low nibble
    assert reference(shadow)[0] == 0x41
    for y, expected in ((0, 0), (1, 8192), (2, 16384), (3, 24576),
                        (4, 160), (199, 32575)):
        shadow = bytearray(32768)
        x = 319 if y == 199 else 0
        for plane in range(4):
            shadow[y*160+plane*40+x//8] = 0x80 >> (x%8)
        packed = reference(shadow)
        assert packed[expected] == (0x0F if x%2 else 0xF0)


def verify(directory, shadow):
    raw = (directory / 'VRAM.BIN').read_bytes()
    expected = reference(shadow)
    if raw != expected:
        errors = [(i, a, b) for i, (a,b) in enumerate(zip(raw, expected)) if a != b]
        raise AssertionError(f'VRAM mismatch: size={len(raw)}, first differences={errors[:12]}')
    assert (directory / 'AFTER.BIN').read_bytes() == shadow, 'Shadow or trailing guard changed'
    metadata = dict(zip(FIELDS, struct.unpack('<' + 'H'*len(FIELDS), (directory / 'META.BIN').read_bytes())))
    assert metadata['block_end'] == 0x9c00
    assert metadata['live_end'] <= 0x9800
    assert metadata['psp'] < metadata['code_segment'] <= metadata['shadow_segment']
    assert metadata['shadow_segment'] + 0x800 <= metadata['stack_segment']
    assert metadata['stack_segment'] < metadata['live_end']
    assert metadata['bios_mode'] == 9 and metadata['bios_columns'] == 40
    assert metadata['bios_kb_before'] == metadata['bios_kb_after'] == 624
    for field in ('alias_verified', 'mcb_verified', 'disabled_verified', 'registers_verified'):
        assert metadata[field] == 1, field
    colours, packed, pixels, rgb = set(), set(), 0, bytearray()
    for y in range(200):
        for x in range(320):
            address = (y & 3)*0x2000 + (y >> 2)*160 + (x >> 1)
            actual = (raw[address] >> (4 if x % 2 == 0 else 0)) & 15
            assert actual == pixel(shadow, x, y), (x, y, actual)
            colours.add(actual)
            packed.add(raw[address])
            pixels += 1
            rgb.extend(PALETTE[actual])
    assert colours == set(range(16)), 'All 16 RGBI values must be exercised'
    for bank in range(4):
        assert raw[bank*8192+8000:(bank+1)*8192] == bytes([SENTINEL])*192
    ppm = b'P6\n320 200\n255\n' + rgb
    (directory / 'FRAME.PPM').write_bytes(ppm)
    try:
        from PIL import Image
        Image.frombytes('RGB', (320, 200), bytes(rgb)).save(directory / 'FRAME.PNG')
    except ImportError:
        pass  # PPM is the dependency-free exact 320x200 decoded dump.
    plane_values = [len({shadow[y*160+p*40+x] for y in range(200) for x in range(40)}) for p in range(4)]
    start = metadata['tick_start_high']*65536 + metadata['tick_start_low']
    end = metadata['tick_end_high']*65536 + metadata['tick_end_low']
    ticks = (end - start) % 0x1800B0
    timing = None
    if metadata['benchmark_frames']:
        assert ticks > 0, 'Benchmark must span at least one BIOS timer tick'
        frames = metadata['benchmark_frames']
        seconds = ticks * 65536 / (14318180 / 12)
        timing = dict(frames=frames, bios_ticks=ticks, elapsed_seconds=seconds,
                      seconds_per_frame=seconds/frames, frames_per_second=frames/seconds,
                      resolution_seconds=65536/(14318180/12),
                      cycles=20000, units='DOSBox-X emulated BIOS timer, not real-hardware timing',
                      excludes='GDI, Windows scheduling and cursor drawing; cursor calls are far stubs')
    return dict(metadata=metadata, timing=timing, visible_bytes=32000, verified_pixels=pixels,
                padding_bytes=768, colours=len(colours), packed_values=len(packed),
                input_values_per_plane=plane_values,
                vram_sha256=hashlib.sha256(raw).hexdigest(),
                image='FRAME.PNG' if (directory / 'FRAME.PNG').exists() else 'FRAME.PPM')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=HERE.parents[1])
    parser.add_argument('--dosbox', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--timeout', type=int, default=90)
    args = parser.parse_args()
    repo, dosbox, out = args.repo.resolve(), args.dosbox.resolve(), args.out.resolve()
    if not 1 <= args.timeout <= 300:
        parser.error('--timeout must be between 1 and 300 seconds per emulator boot')
    validate_reference()
    if out.exists():
        parser.error('--out must be a fresh directory')
    out.mkdir(parents=True)
    build = out / 'build'
    build.mkdir()
    # Mount ONLY disposable test data/tools; never the repository or Windows.
    for tool in ('MASM.EXE', 'LINK4.EXE'):
        shutil.copyfile(repo / 'BIN' / tool, build / tool)
    body = extract_source(repo)
    dos_text(build / 'FLUSH.ASM', body)
    dos_text(build / 'TESTFB.ASM', source(body))
    dos_text(build / 'RUN.BAT', '@ECHO OFF\nMASM TESTFB.ASM,TESTFB.OBJ,TESTFB.LST; > BUILD.LOG\n'
             'LINK4 TESTFB.OBJ,TESTFB.EXE,TESTFB.MAP; >> BUILD.LOG\nEXIT\n')
    run_dos(dosbox, build, args.timeout)
    log = (build / 'BUILD.LOG').read_text(errors='replace')
    errors = re.findall(r'(\d+)\s+Severe\s+Errors', log)
    if errors != ['0'] or re.search(r'error [AL]\d+|fatal error', log, re.I):
        raise RuntimeError('Assembly/link failed: ' + log)
    results = {}
    for name in ('swatches', 'coverage', 'timing'):
        directory = out / name
        directory.mkdir()
        shutil.copyfile(build / 'TESTFB.EXE', directory / 'TESTFB.EXE')
        shadow = make_shadow('swatches' if name == 'timing' else name)
        (directory / 'SHADOW.BIN').write_bytes(shadow)
        command = 'TESTFB.EXE B' if name == 'timing' else 'TESTFB.EXE'
        dos_text(directory / 'RUN.BAT', '@ECHO OFF\n' + command + ' > TESTFB.LOG\n'
                 'IF ERRORLEVEL 1 GOTO FAIL\nECHO PASS> RESULT.TXT\nGOTO DONE\n'
                 ':FAIL\nECHO FAIL> RESULT.TXT\n:DONE\nEXIT\n')
        run_dos(dosbox, directory, args.timeout, cycles=20000 if name == 'timing' else 200000)
        if (directory / 'RESULT.TXT').read_text().strip() != 'PASS':
            raise RuntimeError('DOS harness failed in ' + name + ': ' + (directory / 'TESTFB.LOG').read_text())
        results[name] = verify(directory, shadow)
    assert results['coverage']['input_values_per_plane'] == [256]*4
    assert results['coverage']['packed_values'] == 256
    assert results['timing']['metadata']['benchmark_frames'] == 16
    assert results['timing']['metadata']['hide_count'] == results['timing']['metadata']['show_count'] == 17
    report = dict(status='PASS', cpu='8086_prefetch (accepted DOSBox-X 8086 core)',
                  memory='640K physical Tandy; BIOS 624K; expanded base memory, XMS, EMS, UMB disabled',
                  resolution=[320,200], cases=results,
                  full_frame_work=dict(planar_groups=8000, converted_pixels=64000, packed_bytes=32000),
                  source_sha256=hashlib.sha256(body.encode('ascii')).hexdigest(),
                  executable_sha256=hashlib.sha256((build/'TESTFB.EXE').read_bytes()).hexdigest(),
                  limits='Standalone exact conversion; cursor stubs; no full Windows or real-hardware timing claim')
    (out / 'RESULT.JSON').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
