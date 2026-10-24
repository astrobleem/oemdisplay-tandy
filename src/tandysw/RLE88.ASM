; Bounded 8086 BI_RLE4/BI_RLE8 row iterator for Windows 3.0 DIB callers.
; The compressed buffer is read-only and is bounded by biSizeImage.
; RLE4 indices expand to one byte each so the existing BI_RGB 8bpp palette
; converter can perform the normal device color translation without a full
; image allocation.  A caller validates once, resets, then streams rows.
?PLM=1
?WIN=1
include cmacros.inc
include gdidefs.inc
include display.inc
.8086

externFP DeviceBitmapBits
externFP BitBlt
externFP GlobalAlloc
externFP GlobalLock
externFP GlobalFree
externA __NEXTSEG

rsSrcOff    equ 0
rsSrcSeg    equ 2
rsSizeLo    equ 4
rsSizeHi    equ 6
rsPosLo     equ 8
rsPosHi     equ 10
rsWidth     equ 12
rsHeight    equ 14
rsX         equ 16
rsY         equ 18
rsDepth     equ 20
rsComp      equ 22
rsNextSeg   equ 24
rsFlags     equ 26
rsSkip      equ 27
rsDeltaX    equ 28
rsRowPitch  equ 30
rsPalette   equ 32
rsReadByte  equ 34
rsBytes     equ 36

rleEob      equ 00000001b
rleDelta    equ 00000010b

sBegin Code
assumes cs,Code
assumes ds,nothing
assumes es,nothing

; Expand every conditional into a short local branch plus an ordinary
; near jump.  MASM 5.1 does not relax out-of-range 8086 conditional branches.
rle_branch macro condition,target
local taken,not_taken
    condition taken
    jmp short not_taken
taken:
    jmp target
not_taken:
endm

; Initialize caller-owned state.  The size is the exact maximum readable
; range; zero-sized compressed input is rejected because this ABI has no
; separate compressed-buffer length.
cProc RLEInit,<FAR,PUBLIC,WIN,PASCAL>,<si,di,es>
    parmD lpState
    parmD lpBits
    parmD cbBits
    parmW mapWidth
    parmW mapHeight
    parmW bitCount
    parmW compression
    parmW nextSegment
    parmW paletteColors
cBegin
    cld
    les di,lpState
    mov ax,es
    or ax,di
    rle_branch jz,rlei_bad
    cmp word ptr lpBits,0
    rle_branch jne,rlei_have_bits
    cmp word ptr lpBits+2,0
    rle_branch je,rlei_bad
rlei_have_bits:
    mov ax,word ptr cbBits
    or ax,word ptr cbBits+2
    rle_branch jz,rlei_bad
    mov ax,mapWidth
    or ax,ax
    rle_branch jle,rlei_bad
    cmp ax,7fffh
    rle_branch ja,rlei_bad
    mov ax,mapHeight
    or ax,ax
    rle_branch jle,rlei_bad
    cmp ax,7fffh
    rle_branch ja,rlei_bad
    mov ax,compression
    cmp ax,1
    rle_branch je,rlei_rle8
    cmp ax,2
    rle_branch jne,rlei_bad
    cmp bitCount,4
    rle_branch jne,rlei_bad
    jmp short rlei_format_ok
rlei_rle8:
    cmp bitCount,8
    rle_branch jne,rlei_bad
rlei_format_ok:
    mov ax,nextSegment
    or ax,ax
    rle_branch jz,rlei_bad
    mov ax,paletteColors
    or ax,ax
    rle_branch jz,rlei_bad
    cmp compression,1
    rle_branch jne,rlei_palette4
    cmp ax,256
    rle_branch ja,rlei_bad
    jmp short rlei_palette_ok
rlei_palette4:
    cmp ax,16
    rle_branch ja,rlei_bad
rlei_palette_ok:
    xor ax,ax
    mov cx,rsBytes/2
    rep stosw
    les di,lpState
    mov ax,word ptr lpBits
    mov es:[di+rsSrcOff],ax
    mov ax,word ptr lpBits+2
    mov es:[di+rsSrcSeg],ax
    mov ax,word ptr cbBits
    mov es:[di+rsSizeLo],ax
    mov ax,word ptr cbBits+2
    mov es:[di+rsSizeHi],ax
    mov ax,mapWidth
    mov es:[di+rsWidth],ax
    mov ax,mapHeight
    mov es:[di+rsHeight],ax
    mov ax,bitCount
    mov es:[di+rsDepth],ax
    mov ax,compression
    mov es:[di+rsComp],ax
    mov ax,nextSegment
    mov es:[di+rsNextSeg],ax
    mov ax,paletteColors
    mov es:[di+rsPalette],ax
    ; Expanded output is an 8bpp BI_RGB row with DWORD pitch.
    mov ax,mapWidth
    add ax,3
    rle_branch jc,rlei_bad
    and ax,0fffch
    mov es:[di+rsRowPitch],ax
    mov ax,1
    jmp short rlei_exit
rlei_bad:
    xor ax,ax
rlei_exit:
cEnd

; Read one bounded stream byte.  ES:DI addresses RLESTATE.  The pointer is a
; huge-pointer sequence using the driver's __NEXTSEG increment at 64K wrap.
rle_read_byte proc near
    mov ax,es:[di+rsPosHi]
    cmp ax,es:[di+rsSizeHi]
    rle_branch ja,rleb_bad
    rle_branch jb,rleb_have_byte
    mov ax,es:[di+rsPosLo]
    cmp ax,es:[di+rsSizeLo]
    rle_branch jae,rleb_bad
rleb_have_byte:
    push ds
    mov ax,es:[di+rsSrcSeg]
    mov ds,ax
    mov si,es:[di+rsSrcOff]
    mov al,ds:[si]
    mov es:[di+rsReadByte],al
    inc si
    rle_branch jnz,rleb_no_wrap
    push ax
    mov ax,ds
    add ax,es:[di+rsNextSeg]
    rle_branch jc,rleb_segment_overflow_pop
    mov ds,ax
    pop ax
rleb_no_wrap:
    mov es:[di+rsSrcOff],si
    mov es:[di+rsSrcSeg],ds
    pop ds
    mov ax,es:[di+rsPosLo]
    inc ax
    mov es:[di+rsPosLo],ax
    rle_branch jnz,rleb_ok
    inc word ptr es:[di+rsPosHi]
rleb_ok:
    mov al,es:[di+rsReadByte]
    clc
    ret
rleb_segment_overflow_pop:
    pop ax
rleb_segment_overflow:
    pop ds
rleb_bad:
    stc
    ret
rle_read_byte endp

; Return 1 with DX=bottom-up scan index for each decoded row, 2 after a valid
; EOB and all implicit zero rows, or 0 for malformed/truncated input.
cProc RLENextRow,<FAR,PUBLIC,WIN,PASCAL>,<si,di,es>
    parmD lpState
    parmD lpRow
    localW rowPitch
    localW runCount
    localW runIndex
    localW runValue
    localW payloadBytes
    localW payloadLeft
    localW absoluteCount
    localW startX
    localW scanIndex
    localW storeX
    localB padFlag
    localB storeVal
    localB rowDepth
cBegin
    cld
    les di,lpState
    mov ax,es
    or ax,di
    rle_branch jz,rlen_bad
    mov ax,es:[di+rsRowPitch]
    mov rowPitch,ax
    mov ax,es:[di+rsDepth]
    mov rowDepth,al
    ; Clear one bounded row.  Expanded 8bpp output is scratch only; NULL is
    ; used by the validation pass and performs no writes.
    mov ax,word ptr lpRow
    or ax,word ptr lpRow+2
    rle_branch jz,rlen_no_zero
    les di,lpRow
    xor ax,ax
    mov cx,rowPitch
    rep stosb
rlen_no_zero:
    les di,lpState
    mov al,es:[di+rsFlags]
    test al,rleEob
    rle_branch jz,rlen_pending
    mov ax,es:[di+rsY]
    cmp ax,es:[di+rsHeight]
    rle_branch jae,rlen_done
    mov scanIndex,ax
    inc ax
    mov es:[di+rsY],ax
    mov dx,scanIndex
    mov ax,1
    jmp rlen_exit

rlen_pending:
    test al,rleDelta
    rle_branch jz,rlen_command
    cmp byte ptr es:[di+rsSkip],0
    rle_branch jz,rlen_apply_delta_x
    mov ax,es:[di+rsY]
    cmp ax,es:[di+rsHeight]
    rle_branch jae,rlen_bad
    mov scanIndex,ax
    inc ax
    mov es:[di+rsY],ax
    dec byte ptr es:[di+rsSkip]
    mov word ptr es:[di+rsX],0
    mov dx,scanIndex
    mov ax,1
    jmp rlen_exit
rlen_apply_delta_x:
    mov ax,es:[di+rsDeltaX]
    mov es:[di+rsX],ax
    and byte ptr es:[di+rsFlags],not rleDelta

rlen_command:
    les di,lpState
    call rle_read_byte
    rle_branch jc,rlen_bad
    xor ah,ah
    mov runCount,ax
    call rle_read_byte
    rle_branch jc,rlen_bad
    xor ah,ah
    mov runValue,ax
    mov ax,runCount
    or ax,ax
    rle_branch jz,rlen_escape
    ; Encoded run must fit entirely in the current bottom-up scan.
    les di,lpState
    mov ax,es:[di+rsY]
    cmp ax,es:[di+rsHeight]
    rle_branch jae,rlen_bad
    mov ax,es:[di+rsX]
    mov startX,ax
    add ax,runCount
    rle_branch jc,rlen_bad
    cmp ax,es:[di+rsWidth]
    rle_branch ja,rlen_bad
    mov runIndex,0
    cmp rowDepth,8
    rle_branch jne,rlen_encoded4
    les di,lpState
    mov ax,es:[di+rsPalette]
    xor ah,ah
    mov al,byte ptr runValue
    cmp ax,es:[di+rsPalette]
    rle_branch jae,rlen_bad
    mov ax,word ptr lpRow
    or ax,word ptr lpRow+2
    rle_branch jz,rlen_encoded8_advance
    les di,lpRow
    mov bx,startX
    add di,bx
    mov al,byte ptr runValue
    mov cx,runCount
    rep stosb
rlen_encoded8_advance:
    les di,lpState
    mov ax,es:[di+rsX]
    add ax,runCount
    mov es:[di+rsX],ax
    jmp rlen_command
rlen_encoded4:
    mov ax,runIndex
    cmp ax,runCount
    rle_branch jae,rlen_encoded_done
    mov bx,runIndex
    mov al,byte ptr runValue
    test bl,1
    rle_branch jnz,rlen_encoded_low
    shr al,1
    shr al,1
    shr al,1
    shr al,1
rlen_encoded_low:
    and al,0fh
    mov storeVal,al
    mov ax,startX
    add ax,runIndex
    mov storeX,ax
    call rle_store_pixel
    rle_branch jc,rlen_bad
    inc runIndex
    jmp rlen_encoded4
rlen_encoded_done:
    les di,lpState
    mov ax,es:[di+rsX]
    add ax,runCount
    mov es:[di+rsX],ax
    jmp rlen_command

rlen_escape:
    mov ax,runValue
    cmp ax,0
    rle_branch je,rlen_eol
    cmp ax,1
    rle_branch je,rlen_eob
    cmp ax,2
    rle_branch je,rlen_delta
    ; Absolute mode (3..255). Bound the entire run before consuming payload.
    les di,lpState
    mov ax,es:[di+rsY]
    cmp ax,es:[di+rsHeight]
    rle_branch jae,rlen_bad
    mov ax,es:[di+rsX]
    mov startX,ax
    add ax,runValue
    rle_branch jc,rlen_bad
    cmp ax,es:[di+rsWidth]
    rle_branch ja,rlen_bad
    mov ax,runValue
    mov payloadLeft,ax
    mov absoluteCount,ax
    mov runIndex,0
    cmp rowDepth,8
    rle_branch jne,rlen_absolute4_start
    mov payloadBytes,ax
    jmp rlen_absolute8_loop
rlen_absolute4_start:
    inc ax
    shr ax,1
    mov payloadBytes,ax
    mov padFlag,0
    test al,1
    rle_branch jz,rlen_absolute4_loop
    mov padFlag,1
rlen_absolute4_loop:
    mov ax,payloadBytes
    or ax,ax
    rle_branch jz,rlen_absolute_pad
    les di,lpState
    call rle_read_byte
    rle_branch jc,rlen_bad
    mov byte ptr runValue+1,al
    mov al,byte ptr runValue+1
    shr al,1
    shr al,1
    shr al,1
    shr al,1
    mov storeVal,al
    mov ax,startX
    add ax,runIndex
    mov storeX,ax
    call rle_store_pixel
    rle_branch jc,rlen_bad
    inc runIndex
    dec word ptr payloadLeft
    rle_branch jz,rlen_absolute4_byte_done
    mov al,byte ptr runValue+1
    and al,0fh
    mov storeVal,al
    mov ax,startX
    add ax,runIndex
    mov storeX,ax
    call rle_store_pixel
    rle_branch jc,rlen_bad
    inc runIndex
    dec word ptr payloadLeft
rlen_absolute4_byte_done:
    dec word ptr payloadBytes
    jmp rlen_absolute4_loop

rlen_absolute8_loop:
    mov ax,payloadLeft
    or ax,ax
    rle_branch jz,rlen_absolute_pad
    les di,lpState
    call rle_read_byte
    rle_branch jc,rlen_bad
    mov storeVal,al
    mov ax,startX
    add ax,runIndex
    mov storeX,ax
    call rle_store_pixel
    rle_branch jc,rlen_bad
    inc runIndex
    dec word ptr payloadLeft
    dec word ptr payloadBytes
    jmp rlen_absolute8_loop

rlen_absolute_pad:
    cmp rowDepth,8
    rle_branch jne,rlen_absolute4_pad
    test byte ptr absoluteCount,1
    rle_branch jz,rlen_absolute_done
    jmp short rlen_read_pad
rlen_absolute4_pad:
    cmp padFlag,0
    rle_branch jne,rlen_read_pad
    jmp short rlen_absolute_done
rlen_read_pad:
    les di,lpState
    call rle_read_byte
    rle_branch jc,rlen_bad
rlen_absolute_done:
    les di,lpState
    mov ax,es:[di+rsX]
    add ax,absoluteCount
    mov es:[di+rsX],ax
    jmp rlen_command

rlen_eol:
    les di,lpState
    mov ax,es:[di+rsY]
    cmp ax,es:[di+rsHeight]
    rle_branch jae,rlen_bad
    mov scanIndex,ax
    inc ax
    mov es:[di+rsY],ax
    mov word ptr es:[di+rsX],0
    mov dx,scanIndex
    mov ax,1
    jmp rlen_exit

rlen_eob:
    les di,lpState
    mov ax,es:[di+rsY]
    cmp ax,es:[di+rsHeight]
    rle_branch ja,rlen_bad
    or byte ptr es:[di+rsFlags],rleEob
    cmp ax,es:[di+rsHeight]
    rle_branch jae,rlen_done
    mov scanIndex,ax
    inc ax
    mov es:[di+rsY],ax
    mov word ptr es:[di+rsX],0
    mov dx,scanIndex
    mov ax,1
    jmp rlen_exit

rlen_delta:
    les di,lpState
    call rle_read_byte
    rle_branch jc,rlen_bad
    xor ah,ah
    mov runIndex,ax             ; delta X
    call rle_read_byte
    rle_branch jc,rlen_bad
    xor ah,ah
    mov runCount,ax             ; delta Y
    mov ax,es:[di+rsX]
    add ax,runIndex
    rle_branch jc,rlen_bad
    cmp ax,es:[di+rsWidth]
    rle_branch ja,rlen_bad
    mov startX,ax              ; validated absolute X + dx
    mov ax,es:[di+rsY]
    add ax,runCount
    rle_branch jc,rlen_bad
    cmp ax,es:[di+rsHeight]
    rle_branch jae,rlen_bad
    cmp runCount,0
    rle_branch je,rlen_delta_same_row
    ; Finish the current row; skipped rows are returned as zero rows before
    ; the target row resumes at the saved absolute X + dx.
    mov ax,es:[di+rsY]
    cmp ax,es:[di+rsHeight]
    rle_branch jae,rlen_bad
    mov scanIndex,ax
    mov ax,startX
    mov es:[di+rsDeltaX],ax
    mov ax,runCount
    dec ax
    mov es:[di+rsSkip],al
    or byte ptr es:[di+rsFlags],rleDelta
    mov ax,es:[di+rsY]
    inc ax
    mov es:[di+rsY],ax
    mov word ptr es:[di+rsX],0
    mov dx,scanIndex
    mov ax,1
    jmp rlen_exit
rlen_delta_same_row:
    mov ax,es:[di+rsX]
    add ax,runIndex
    mov es:[di+rsX],ax
    jmp rlen_command

rlen_done:
    mov ax,2
    jmp rlen_exit
rlen_bad:
    xor ax,ax
    jmp short rlen_exit

; Emit one expanded index.  Kept inside RLENextRow so all stack-local
; parameters remain in scope for MASM and the validator shares this path.
rle_store_pixel:
    les di,lpState
    xor ax,ax
    mov al,storeVal
    cmp ax,es:[di+rsPalette]
    rle_branch jae,rlesp_bad
    mov ax,word ptr lpRow
    or ax,word ptr lpRow+2
    rle_branch jz,rlesp_ok
    les di,lpRow
    mov bx,storeX
    mov al,storeVal
    mov es:[di+bx],al
rlesp_ok:
    clc
    retn
rlesp_bad:
    stc
    retn

rlen_exit:
cEnd

; Compressed SetDIBits path for the public DeviceBitmapBits entrypoint.  It
; validates the entire stream before converting or blitting any row, then
; uses the existing BI_RGB converter on one expanded scan at a time.
cProc RLESetDeviceBitmapBits,<FAR,PUBLIC,WIN,PASCAL>,<si,di,ds,es>
    parmD lp_pdevice
    parmW setOrGet
    parmW startScan
    parmW numScans
    parmD lp_bits
    parmD lp_bi
    parmD lpDrawMode
    parmD dwColorInfo
    localW heapHandle
    localW resultScans
    localW driverDS
    localW mapWidth
    localW mapHeight
    localW nextSegment
    localW bitCount
    localW compression
    localW paletteColors
    localW headerBytes
    localW rowPitch
    localW ownStride
    localW allocationBytes
    localW scanLimit
    localW scanNow
    localW validateRowsLeft
    localW destY
    localW destHeight
    localW destWidth
    localW xCount
    localW zeroWord
    localW oneWord
    localD sizeImage
    localD privateInfo
    localD rleRowBits
    localD rowBits
    localD rleStatePtr
    localD rowDevice
    localD destDevice
    localD nullPointer
    localD copyRop
    localV rleState,36
    localV rowBitmap,32
cBegin
    cld
    mov driverDS,ds
    xor ax,ax
    mov heapHandle,ax
    mov resultScans,ax
    mov zeroWord,ax
    mov ax,__NEXTSEG
    mov nextSegment,ax
    mov word ptr nullPointer,0
    mov word ptr nullPointer+2,0
    mov oneWord,1
    mov word ptr copyRop,0020h
    mov word ptr copyRop+2,00cch
    ; BI_RLE4/8 are input encodings. GetDIBits would require an encoder.
    cmp setOrGet,0
    rle_branch jne,rles_return
    cmp numScans,0
    rle_branch je,rles_return
    les di,lp_pdevice
    mov ax,es
    or ax,di
    rle_branch jz,rles_return
    cmp word ptr es:[di].bmType,0
    rle_branch jne,rles_return
    mov ax,es:[di].bmWidth
    or ax,ax
    rle_branch jle,rles_return
    mov destWidth,ax
    mov ax,es:[di].bmHeight
    or ax,ax
    rle_branch jle,rles_return
    mov destHeight,ax
    les di,lp_bits
    mov ax,es
    or ax,di
    rle_branch jz,rles_return
    les di,lp_bi
    mov ax,es
    or ax,di
    rle_branch jz,rles_return
    cmp di,0ffd8h
    rle_branch ja,rles_return
    cmp word ptr es:[di].biSize,40
    rle_branch jne,rles_return
    cmp word ptr es:[di].biSize+2,0
    rle_branch jne,rles_return
    cmp es:[di].biPlanes,1
    rle_branch jne,rles_return
    mov ax,word ptr es:[di].biWidth
    or ax,ax
    rle_branch jle,rles_return
    cmp word ptr es:[di].biWidth+2,0
    rle_branch jne,rles_return
    cmp ax,7fffh
    rle_branch ja,rles_return
    mov mapWidth,ax
    mov ax,word ptr es:[di].biHeight
    or ax,ax
    rle_branch jle,rles_return
    cmp word ptr es:[di].biHeight+2,0
    rle_branch jne,rles_return
    cmp ax,7fffh
    rle_branch ja,rles_return
    mov mapHeight,ax
    mov ax,es:[di].biBitCount
    mov bitCount,ax
    mov ax,word ptr es:[di].biCompression+2
    or ax,ax
    rle_branch jnz,rles_return
    mov ax,word ptr es:[di].biCompression
    mov compression,ax
    cmp ax,1
    rle_branch je,rles_check8
    cmp ax,2
    rle_branch jne,rles_return
    cmp bitCount,4
    rle_branch jne,rles_return
    mov ax,16
    jmp short rles_palette_limit
rles_check8:
    cmp bitCount,8
    rle_branch jne,rles_return
    mov ax,256
rles_palette_limit:
    mov paletteColors,ax
    mov ax,word ptr es:[di].biClrUsed+2
    or ax,ax
    rle_branch jnz,rles_return
    mov ax,word ptr es:[di].biClrUsed
    or ax,ax
    rle_branch jz,rles_palette_ready
    cmp ax,paletteColors
    rle_branch ja,rles_return
    mov paletteColors,ax
rles_palette_ready:
    mov ax,word ptr es:[di].biSizeImage
    mov dx,word ptr es:[di].biSizeImage+2
    mov word ptr sizeImage,ax
    mov word ptr sizeImage+2,dx
    or ax,dx
    rle_branch jz,rles_return
    mov ax,paletteColors
    shl ax,1
    shl ax,1
    add ax,40
    rle_branch jc,rles_return
    mov headerBytes,ax
    ; A palette is allowed to cross a huge-pointer segment boundary, but the
    ; 40-byte BITMAPINFOHEADER itself was checked contiguous above.
    mov ax,di
    add ax,headerBytes
    rle_branch jnc,rles_band
    mov ax,es
    add ax,__NEXTSEG
    rle_branch jc,rles_return
rles_band:
    mov ax,startScan
    cmp ax,mapHeight
    rle_branch jae,rles_return
    mov dx,mapHeight
    sub dx,ax
    mov ax,numScans
    cmp ax,dx
    rle_branch jbe,rles_scan_limit
    mov ax,dx
rles_scan_limit:
    add ax,startScan
    rle_branch jc,rles_return
    mov scanLimit,ax
    lea ax,rleState
    mov word ptr rleStatePtr,ax
    mov word ptr rleStatePtr+2,ss
    cCall RLEInit,<rleStatePtr,lp_bits,sizeImage,mapWidth,mapHeight,bitCount,compression,nextSegment,paletteColors>
    cmp ax,1
    rle_branch jne,rles_return
    mov ax,mapHeight
    mov scanNow,ax
rles_validate:
    cCall RLENextRow,<rleStatePtr,nullPointer>
    cmp ax,1
    rle_branch jne,rles_return
    dec scanNow
    rle_branch jnz,rles_validate
    cCall RLENextRow,<rleStatePtr,nullPointer>
    cmp ax,2
    rle_branch jne,rles_return
    ; Expanded row is <=32768 bytes; planar row is <=16384.  The fixed block
    ; remains below 64K and below the conventional-memory budget.
    mov ax,mapWidth
    add ax,3
    rle_branch jc,rles_return
    and ax,0fffch
    mov rowPitch,ax
    mov ax,mapWidth
    add ax,15
    rle_branch jc,rles_return
    and ax,0fff0h
    shr ax,1
    shr ax,1
    shr ax,1
    mov ownStride,ax
    shl ax,1
    shl ax,1
    add ax,1064
    rle_branch jc,rles_return
    add ax,rowPitch
    rle_branch jc,rles_return
    mov allocationBytes,ax
    xor ax,ax
    mov bx,0040h
    cCall GlobalAlloc,<bx,ax,allocationBytes>
    or ax,ax
    rle_branch jz,rles_return
    mov heapHandle,ax
    cCall GlobalLock,<heapHandle>
    mov bx,ax
    or bx,dx
    rle_branch jz,rles_cleanup
    mov word ptr privateInfo,ax
    mov word ptr privateInfo+2,dx
    mov bx,ax
    add bx,allocationBytes
    rle_branch jc,rles_cleanup
    add ax,1064
    rle_branch jc,rles_cleanup
    mov word ptr rleRowBits,ax
    mov word ptr rleRowBits+2,dx
    add ax,rowPitch
    adc dx,0
    rle_branch jc,rles_cleanup
    mov word ptr rowBits,ax
    mov word ptr rowBits+2,dx

    ; Preserve the source header and palette; only the private copy becomes
    ; an uncompressed one-row 8bpp DIB for the existing color translator.
    les di,privateInfo
    lds si,lp_bi
    mov cx,headerBytes
rles_copy_header:
    movsb
    or si,si
    rle_branch jnz,rles_copy_no_wrap
    mov ax,ds
    add ax,__NEXTSEG
    rle_branch jc,rles_cleanup
    mov ds,ax
rles_copy_no_wrap:
    loop rles_copy_header
    ; The caller BITMAPINFO may occupy another segment and its palette may
    ; cross a 64K boundary.  Restore the driver's data segment before touching
    ; private locals/data or entering the DDK converter and BitBlt routines.
    mov ax,driverDS
    mov ds,ax
    les di,privateInfo
    mov word ptr es:[di].biHeight,1
    mov word ptr es:[di].biHeight+2,0
    mov word ptr es:[di].biCompression,0
    mov word ptr es:[di].biCompression+2,0
    mov word ptr es:[di].biBitCount,8
    mov ax,paletteColors
    mov word ptr es:[di].biClrUsed,ax
    mov word ptr es:[di].biClrUsed+2,0
    mov ax,rowPitch
    mov word ptr es:[di].biSizeImage,ax
    mov word ptr es:[di].biSizeImage+2,0

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
    mov ax,word ptr lp_pdevice
    mov word ptr destDevice,ax
    mov ax,word ptr lp_pdevice+2
    mov word ptr destDevice+2,ax
    mov ax,destWidth
    cmp ax,mapWidth
    rle_branch jbe,rles_width_ready
    mov ax,mapWidth
rles_width_ready:
    mov xCount,ax
    cCall RLEInit,<rleStatePtr,lp_bits,sizeImage,mapWidth,mapHeight,bitCount,compression,nextSegment,paletteColors>
    cmp ax,1
    rle_branch jne,rles_cleanup
    mov ax,mapHeight
    mov validateRowsLeft,ax
rles_decode:
    cCall RLENextRow,<rleStatePtr,rleRowBits>
    cmp ax,1
    rle_branch jne,rles_cleanup
    mov scanNow,dx
    mov ax,scanNow
    cmp ax,startScan
    rle_branch jb,rles_next_scan
    cmp ax,scanLimit
    rle_branch jae,rles_next_scan
    mov ax,mapHeight
    dec ax
    sub ax,scanNow
    rle_branch jc,rles_next_scan
    cmp ax,destHeight
    rle_branch jae,rles_next_scan
    mov destY,ax
    cCall DeviceBitmapBits,<rowDevice,zeroWord,zeroWord,oneWord,rleRowBits,privateInfo,lpDrawMode,dwColorInfo>
    cmp ax,1
    rle_branch jne,rles_cleanup
    cCall BitBlt,<destDevice,zeroWord,destY,rowDevice,zeroWord,zeroWord,xCount,oneWord,copyRop,nullPointer,lpDrawMode>
    or ax,ax
    rle_branch jz,rles_cleanup
    inc resultScans
rles_next_scan:
    dec validateRowsLeft
    rle_branch jz,rles_cleanup
    jmp rles_decode

rles_cleanup:
    mov ax,driverDS
    mov ds,ax
    cmp heapHandle,0
    rle_branch je,rles_return
    cCall GlobalFree,<heapHandle>
rles_return:
    mov ax,resultScans
cEnd

sEnd Code
end
