; 8086/8088 shadow-only DIBScreenBlt (display ordinal 21).
; ABI and bottom-up band mapping follow DDK DISCREEN.ASM. No EGA I/O.
; A fixed, zero-initialized allocation holds a private BITMAPINFO and ONE
; scan-interleaved four-plane row. Only memory BitBlt writes the shadow;
; FlushShadow runs once, after conversion of the visible band.
; lp_bits begins at StartScan's supplied band, not the full DIB origin.
?PLM=1
?WIN=1
incDevice=1
include cmacros.inc
include gdidefs.inc
include display.inc
.8086
externFP DeviceBitmapBits
externFP RLEInit
externFP RLENextRow
externFP BitBlt
externFP GlobalAlloc
externFP GlobalLock
externFP GlobalFree
externA __NEXTSEG

sBegin Data
extrn shadow_device:BYTE
extrn enabled_flag:BYTE
sEnd Data

sBegin Code
assumes cs,Code
assumes ds,Data
assumes es,nothing
externNP FlushShadow

; Inverse-condition branch over a NEAR failure jump: never depends on
; assembler relaxation or a conditional branch exceeding 8086's 8-bit span.
sd_require macro condition
local good
    condition good
    jmp sd_cleanup
good:
endm

; MASM 5.1 does not expand conditional branches beyond the 8086 short span.
sd_branch macro condition,target
local taken,not_taken
    condition taken
    jmp short not_taken
taken:
    jmp target
not_taken:
endm

cProc DIBScreenBlt,<FAR,PUBLIC,WIN,PASCAL>,<si,di>
    parmD lp_pdevice
    parmW ScrXorg
    parmW ScrYorg
    parmW StartScan
    parmW NumScan
    parmD lpClipRect
    parmD lpDrawMode
    parmD lp_bits
    parmD lp_bi
    parmD dwColorInfo
    localW heapHandle
    localW driverDS
    localW resultScans
    localW mapWidth
    localW mapHeight
    localW nextSegment
    localW bitCount
    localW compression
    localW paletteColors
    localW compressedFlag
    localW headerBytes
    localW ownStride
    localW allocationBytes
    localW xDst
    localW yDst
    localW xSrc
    localW xCount
    localW rowCount
    localW validateRowsLeft
    localW clippedTop
    localW clippedBottom
    localW bandScans
    localW skipScans
    localW firstRleScan
    localW lastRleScan
    localW decodedScan
    localD dibPitch
    localD privateInfo
    localD rowBits
    localD rowDevice
    localD screenDevice
    localD sourceBits
    localD rleSize
    localD rleStatePtr
    localD rleRowBits
    localV rleState,36
    localD nullPointer
    localD copyRop
    localW zeroWord
    localW oneWord
    localV rowBitmap,32
cBegin
    cld
    mov driverDS,ds
    xor ax,ax
    mov heapHandle,ax
    mov resultScans,ax
    mov compressedFlag,ax
    mov ax,__NEXTSEG
    mov nextSegment,ax
    xor bx,bx
    mov zeroWord,bx
    mov word ptr nullPointer,bx
    mov word ptr nullPointer+2,bx
    mov oneWord,1
    mov word ptr copyRop,0020h
    mov word ptr copyRop+2,00cch
    cmp enabled_flag,0
    sd_require jne

    les di,lp_pdevice
    mov ax,es
    or ax,di
    sd_require jnz
    cmp word ptr es:[di].bmType,0
    sd_require jne
    les di,lp_bits
    mov ax,es
    or ax,di
    sd_require jnz
    les di,lp_bi
    mov ax,es
    or ax,di
    sd_require jnz
    ; Header itself must be contiguous. Palette copy below is huge-aware.
    cmp di,0ffd8h
    sd_require jbe
    cmp word ptr es:[di].biSize,40
    sd_require je
    cmp word ptr es:[di].biSize+2,0
    sd_require je
    mov ax,word ptr es:[di].biCompression+2
    or ax,ax
    sd_require jz
    mov ax,word ptr es:[di].biCompression
    mov compression,ax
    or ax,ax
    jz sd_compression_ok
    cmp ax,1
    je sd_rle8_format
    cmp ax,2
    sd_require je
    mov ax,1
    mov compressedFlag,ax
    cmp es:[di].biBitCount,4
    sd_require je
    jmp short sd_compression_ok
sd_rle8_format:
    mov ax,1
    mov compressedFlag,ax
    cmp es:[di].biBitCount,8
    sd_require je
sd_compression_ok:
    cmp es:[di].biPlanes,1
    sd_require je
    mov ax,word ptr es:[di].biWidth
    or ax,ax
    sd_require jg
    cmp word ptr es:[di].biWidth+2,0
    sd_require je
    mov mapWidth,ax
    mov ax,word ptr es:[di].biHeight
    or ax,ax
    sd_require jg
    cmp word ptr es:[di].biHeight+2,0
    sd_require je
    mov mapHeight,ax
    mov ax,es:[di].biBitCount
    mov bitCount,ax
    mov bx,2
    cmp ax,1
    je sd_format
    mov bx,16
    cmp ax,4
    je sd_format
    mov bx,256
    cmp ax,8
    je sd_format
    xor bx,bx
    cmp ax,24
    sd_require je
sd_format:
    ; 24-bit BI_RGB may carry an optional reference palette. Its pixels
    ; are direct RGB, so no table needs copying or palette-size validation.
    cmp bitCount,24
    je sd_palette_default
    ; Bound indexed table length. Zero means the complete default table.
    cmp word ptr es:[di].biClrUsed+2,0
    sd_require je
    mov ax,word ptr es:[di].biClrUsed
    or ax,ax
    jz sd_palette_default
    cmp ax,bx
    sd_require jbe
    mov bx,ax
sd_palette_default:
    ; Missing indexed colors are zero-filled and normalized below, including
    ; the second entry when a 1-bit DIB supplies only one palette color.
    mov paletteColors,bx
    shl bx,1
    shl bx,1
    add bx,40
    mov headerBytes,bx
    ; Ensure any palette segment carry is numerically representable.
    mov ax,di
    add ax,bx
    jnc sd_palette_address
    mov ax,es
    add ax,__NEXTSEG
    sd_require jnc
sd_palette_address:
    cmp compressedFlag,0
    je sd_palette_size_ready
    les di,lp_bi
    mov ax,word ptr es:[di].biSizeImage
    mov dx,word ptr es:[di].biSizeImage+2
    mov word ptr rleSize,ax
    mov word ptr rleSize+2,dx
    or ax,dx
    sd_require jnz
sd_palette_size_ready:
    mov ax,StartScan
    cmp ax,mapHeight
    sd_require jb
    mov bx,mapHeight
    sub bx,ax
    mov ax,NumScan
    or ax,ax
    sd_require jnz
    cmp ax,bx
    jbe sd_band_count
    mov ax,bx
sd_band_count:
    mov bandScans,ax

    ; Clamp caller's clip to the physical 320x200 shadow first.
    les di,lpClipRect
    mov ax,es
    or ax,di
    sd_require jnz
    cmp di,0fff8h
    sd_require jbe
    mov ax,es:[di].left
    or ax,ax
    jge sd_clip_left
    xor ax,ax
sd_clip_left:
    mov xDst,ax
    mov bx,es:[di].right
    cmp bx,320
    jle sd_clip_right
    mov bx,320
sd_clip_right:
    cmp ax,bx
    sd_require jl
    ; left=max(clip.left, ScrXorg), with the right side kept bounded.
    cmp ax,ScrXorg
    jge sd_xleft
    mov ax,ScrXorg
    mov xDst,ax
sd_xleft:
    cmp ax,bx
    sd_require jl
    sub bx,ax
    sub ax,ScrXorg
    cmp ax,mapWidth
    sd_require jb
    mov xSrc,ax
    mov cx,mapWidth
    sub cx,ax
    cmp bx,cx
    jbe sd_xcount
    mov bx,cx
sd_xcount:
    mov xCount,bx
    mov ax,es:[di].top
    or ax,ax
    jge sd_clip_top
    xor ax,ax
sd_clip_top:
    mov clippedTop,ax
    mov bx,es:[di].bottom
    cmp bx,200
    jle sd_clip_bottom
    mov bx,200
sd_clip_bottom:
    cmp ax,bx
    sd_require jl
    mov clippedBottom,bx

    ; signed 32-bit mapped bottom = y + height - StartScan.
    ; Range is [-32768,65534]; a negative bottom cannot meet our clip.
    mov ax,ScrYorg
    cwd
    add ax,mapHeight
    adc dx,0
    sub ax,StartScan
    sbb dx,0
    or dx,dx
    sd_require jz
    mov bx,clippedBottom
    cmp ax,bx
    ja sd_ybottom
    mov bx,ax
sd_ybottom:
    cmp bx,clippedTop
    sd_require jg
    sub ax,bx
    mov skipScans,ax
    cmp ax,bandScans
    sd_require jb
    mov cx,bandScans
    sub cx,ax
    mov ax,bx
    sub ax,clippedTop
    cmp cx,ax
    jbe sd_ycount
    mov cx,ax
sd_ycount:
    mov rowCount,cx
    dec bx
    mov yDst,bx
    mov ax,StartScan
    add ax,skipScans
    sd_require jnc
    mov firstRleScan,ax
    add ax,rowCount
    sd_require jnc
    mov lastRleScan,ax

    ; DWORD-aligned source pitch, retaining both words for wide 24-bit DIBs.
    mov ax,mapWidth
    mov cx,bitCount
    cmp compressedFlag,0
    je sd_pitch_bits_ready
    mov cx,8
sd_pitch_bits_ready:
    mul cx
    add ax,31
    adc dx,0
    shr dx,1
    rcr ax,1
    shr dx,1
    rcr ax,1
    shr dx,1
    rcr ax,1
    and ax,0fffch
    mov word ptr dibPitch,ax
    mov word ptr dibPitch+2,dx
    cmp compressedFlag,0
    jne sd_preflight_rle
    ; source offset of the first visible scan = skipScans * pitch.
    mov cx,skipScans
    call sd_multiply_pitch
    sd_require jnc
    add ax,word ptr lp_bits
    adc dx,0
    sd_require jnc
    mov word ptr sourceBits,ax
    mov ax,dx
    mov bx,__NEXTSEG
    mul bx
    or dx,dx
    sd_require jz
    add ax,word ptr lp_bits+2
    sd_require jnc
    mov word ptr sourceBits+2,ax
    ; Preflight through the last visible scan, including pitch padding.
    ; Thus pointer arithmetic failure cannot happen after any display write.
    mov cx,rowCount
    call sd_multiply_pitch
    sd_require jnc
    sub ax,1
    sbb dx,0
    add ax,word ptr sourceBits
    adc dx,0
    sd_require jnc
    mov ax,dx
    mov bx,__NEXTSEG
    mul bx
    or dx,dx
    sd_require jz
    add ax,word ptr sourceBits+2
    sd_require jnc
    jmp short sd_source_ready
sd_preflight_rle:
    lea ax,rleState
    mov word ptr rleStatePtr,ax
    mov word ptr rleStatePtr+2,ss
    cCall RLEInit,<rleStatePtr,lp_bits,rleSize,mapWidth,mapHeight,bitCount,compression,nextSegment,paletteColors>
    cmp ax,1
    sd_require je
    mov ax,mapHeight
    mov validateRowsLeft,ax
sd_validate_rle_rows:
    cCall RLENextRow,<rleStatePtr,nullPointer>
    cmp ax,1
    sd_require je
    dec validateRowsLeft
    jnz sd_validate_rle_rows
    cCall RLENextRow,<rleStatePtr,nullPointer>
    cmp ax,2
    sd_require je
sd_source_ready:

    ; WORD-aligned per-plane row <=4096 bytes, four planes <=16384.
    mov ax,mapWidth
    add ax,15
    and ax,0fff0h
    shr ax,1
    shr ax,1
    shr ax,1
    mov ownStride,ax
    shl ax,1
    shl ax,1
    add ax,1064
    sd_require jnc
    cmp compressedFlag,0
    je sd_allocation_size_ready
    add ax,word ptr dibPitch
    sd_require jnc
sd_allocation_size_ready:
    mov allocationBytes,ax
    xor ax,ax
    mov bx,0040h                  ; GMEM_FIXED | GMEM_ZEROINIT
    cCall GlobalAlloc,<bx,ax,allocationBytes>
    or ax,ax
    sd_require jnz
    mov heapHandle,ax
    cCall GlobalLock,<heapHandle>
    mov bx,ax
    or bx,dx
    sd_require jnz
    mov word ptr privateInfo,ax
    mov word ptr privateInfo+2,dx
    mov bx,ax
    add bx,allocationBytes
    sd_require jnc
    mov ax,word ptr privateInfo
    add ax,1064
    sd_require jnc
    mov dx,word ptr privateInfo+2
    mov word ptr rleRowBits,ax
    mov word ptr rleRowBits+2,dx
    cmp compressedFlag,0
    je sd_row_device_pointer
    add ax,word ptr dibPitch
    adc dx,word ptr dibPitch+2
    sd_require jnc
sd_row_device_pointer:
    mov word ptr rowBits,ax
    mov word ptr rowBits+2,dx

    ; Copy the caller's header/palette without ever changing it. Byte copy
    ; permits an RGBQUAD palette to cross a huge-pointer segment boundary.
    les di,privateInfo
    lds si,lp_bi
    mov cx,headerBytes
sd_copy_info:
    movsb
    or si,si
    jnz sd_info_no_wrap
    mov ax,ds
    add ax,__NEXTSEG
    mov ds,ax
sd_info_no_wrap:
    loop sd_copy_info
    mov ax,driverDS
    mov ds,ax
    les di,privateInfo
    mov word ptr es:[di].biHeight,1
    mov word ptr es:[di].biHeight+2,0
    cmp compressedFlag,0
    je sd_private_compression_ready
    mov word ptr es:[di].biCompression,0
    mov word ptr es:[di].biCompression+2,0
    mov word ptr es:[di].biBitCount,8
sd_private_compression_ready:
    ; The converter's translation table is stack storage. Initialize all
    ; indexed entries, including missing palette entries (zero-filled black),
    ; so an out-of-range input index cannot read stale stack translations.
    mov ax,2
    cmp bitCount,1
    je sd_private_colors
    mov ax,16
    cmp bitCount,4
    je sd_private_colors
    mov ax,256
    cmp bitCount,8
    je sd_private_colors
    xor ax,ax
sd_private_colors:
    cmp compressedFlag,0
    je sd_private_color_count
    mov ax,paletteColors
    jmp short sd_private_color_store
sd_private_color_count:
    mov word ptr es:[di].biClrUsed,ax
    jmp short sd_private_image_size
sd_private_color_store:
    mov word ptr es:[di].biClrUsed,ax
sd_private_image_size:
    mov ax,word ptr dibPitch
    mov word ptr es:[di].biSizeImage,ax
    mov ax,word ptr dibPitch+2
    mov word ptr es:[di].biSizeImage+2,ax

    push ss
    pop es
    lea di,rowBitmap
    mov word ptr rowDevice,di
    mov word ptr rowDevice+2,ss
    xor ax,ax
    mov cx,16
    rep stosw
    lea di,rowBitmap
    mov ax,mapWidth
    mov es:[di].bmWidth,ax
    mov es:[di].bmHeight,1
    mov ax,ownStride
    mov es:[di].bmWidthBytes,ax
    mov word ptr es:[di].bmWidthPlanes,ax
    mov word ptr es:[di].bmPlanes,0104h
    mov ax,word ptr rowBits
    mov word ptr es:[di].bmBits,ax
    mov ax,word ptr rowBits+2
    mov word ptr es:[di].bmBits+2,ax
    mov word ptr screenDevice,offset shadow_device
    mov word ptr screenDevice+2,ds

    cmp compressedFlag,0
    sd_branch jne,sd_rle_draw_start
sd_next_row:
    cCall DeviceBitmapBits,<rowDevice,zeroWord,zeroWord,oneWord,sourceBits,privateInfo,lpDrawMode,dwColorInfo>
    cmp ax,1
    sd_branch jne,sd_rows_done
    cCall BitBlt,<screenDevice,xDst,yDst,rowDevice,xSrc,zeroWord,xCount,oneWord,copyRop,nullPointer,lpDrawMode>
    ; All arguments describe fully clipped memory surfaces; preserve the
    ; original engine's return semantics and count only successful rows.
    or ax,ax
    sd_branch jz,sd_rows_done
    inc resultScans
    dec rowCount
    sd_branch jz,sd_rows_done
    dec yDst
    mov ax,word ptr dibPitch
    mov dx,word ptr dibPitch+2
    add word ptr sourceBits,ax
    adc dx,0
    mov ax,dx
    mov bx,__NEXTSEG
    mul bx
    add word ptr sourceBits+2,ax
    jmp sd_next_row

sd_rle_draw_start:
    cmp rowCount,0
    sd_branch je,sd_rows_done
    cCall RLEInit,<rleStatePtr,lp_bits,rleSize,mapWidth,mapHeight,bitCount,compression,nextSegment,paletteColors>
    cmp ax,1
    sd_branch jne,sd_rows_done
sd_rle_next_row:
    cCall RLENextRow,<rleStatePtr,rleRowBits>
    cmp ax,1
    sd_branch jne,sd_rows_done
    mov decodedScan,dx
    mov ax,decodedScan
    cmp ax,firstRleScan
    jb sd_rle_next_row
    cmp ax,lastRleScan
    jae sd_rle_next_row
    mov ax,word ptr rleRowBits
    mov word ptr sourceBits,ax
    mov ax,word ptr rleRowBits+2
    mov word ptr sourceBits+2,ax
    cCall DeviceBitmapBits,<rowDevice,zeroWord,zeroWord,oneWord,sourceBits,privateInfo,lpDrawMode,dwColorInfo>
    cmp ax,1
    jne sd_rows_done
    cCall BitBlt,<screenDevice,xDst,yDst,rowDevice,xSrc,zeroWord,xCount,oneWord,copyRop,nullPointer,lpDrawMode>
    or ax,ax
    jz sd_rows_done
    inc resultScans
    dec rowCount
    jz sd_rows_done
    dec yDst
    jmp sd_rle_next_row
sd_rows_done:
    cmp resultScans,0
    je sd_cleanup
    mov ax,driverDS
    mov ds,ax
    call FlushShadow
sd_cleanup:
    mov ax,driverDS
    mov ds,ax
    cmp heapHandle,0
    je sd_return
    ; Fixed GlobalAlloc blocks do not have a lock count to balance.
    cCall GlobalFree,<heapHandle>
sd_return:
    mov ax,resultScans
cEnd

; CX unsigned scan count, return DX:AX = count * DWORD pitch, CF on overflow.
; Preserves frame/DS; all used registers are volatile at these call sites.
sd_multiply_pitch proc near
    mov ax,word ptr dibPitch+2
    mul cx
    or dx,dx
    jnz sd_pitch_overflow
    mov bx,ax
    mov ax,word ptr dibPitch
    mul cx
    add dx,bx
    ret
sd_pitch_overflow:
    stc
    ret
sd_multiply_pitch endp

sEnd Code
end
