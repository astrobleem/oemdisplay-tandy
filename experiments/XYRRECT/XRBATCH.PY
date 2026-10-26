"""PR155 follow-up: synchronous narrow Output presentation on current XR1.

No pending rows or marker-owned state. Every Output presents before returning.
Use the existing bounded Output gate, XY bank copier and foreground CURKEEP
lease; no interrupt-time GDI call, shadow copy, or new cursor handler.
"""
from pathlib import Path
import importlib.machinery

HERE = Path(__file__).resolve().parent


def patch(renderer):
    rr = importlib.machinery.SourceFileLoader(
        "xr155", str(HERE.parents[1] / "src/rrect/RRPATCH.PY")).load_module()
    p = renderer / "EGA/TSOFT.ASM"
    t = p.read_bytes().decode("latin1")
    def edit(old, new, name):
        nonlocal t
        t = rr.replace_n(t, old.replace("\n", "\r\n"), new.replace("\n", "\r\n"), 1, name)

    # Bound the same validated scanline intervals/polyline points in X.
    edit("    localW lastrow\ncBegin\n    mov dirty,0\n    mov outrows,0\n",
         "    localW lastrow\n    localW firstcol\n    localW lastcol\ncBegin\n    mov dirty,0\n    mov outrows,0\n", "Output X locals")
    edit("    mov cx,count\n    dec cx\nTOutput_scan_interval:\n",
         "    mov firstcol,SCREEN_WIDTH\n    mov lastcol,0\n    mov cx,count\n    dec cx\nTOutput_scan_interval:\n", "scan X initialization")
    edit("    cmp dx,SCREEN_WIDTH\n    or_require jbe,TOutput_render\n    loop TOutput_scan_interval\n",
         """    cmp dx,SCREEN_WIDTH
    or_require jbe,TOutput_render
    cmp bx,firstcol
    jae TOutput_scan_min
    mov firstcol,bx
TOutput_scan_min:
    cmp dx,lastcol
    jbe TOutput_scan_max
    mov lastcol,dx
TOutput_scan_max:
    loop TOutput_scan_interval
""", "scan X bounds")
    edit("    mov cx,count\n    mov ax,7fffh\n    xor bx,bx\nTOutput_poly_point:\n",
         "    mov firstcol,SCREEN_WIDTH\n    mov lastcol,0\n    mov cx,count\n    mov ax,7fffh\n    xor bx,bx\nTOutput_poly_point:\n", "polyline X initialization")
    edit("TOutput_poly_point:\n    mov dx,es:[di]\n    cmp dx,SCREEN_WIDTH\n    or_require jb,TOutput_render\n",
         """TOutput_poly_point:
    mov dx,es:[di]
    cmp dx,SCREEN_WIDTH
    or_require jb,TOutput_render
    cmp dx,firstcol
    jae TOutput_poly_xmin
    mov firstcol,dx
TOutput_poly_xmin:
    inc dx
    cmp dx,lastcol
    jbe TOutput_poly_xmax
    mov lastcol,dx
TOutput_poly_xmax:
""", "polyline X bounds")
    edit("TOutput_line_ordered:\n    mov firstrow,ax\n",
         """TOutput_line_ordered:
    cmp cx,dx
    jbe TOutput_x_ordered
    xchg cx,dx
TOutput_x_ordered:
    mov firstcol,cx
    inc dx
    mov lastcol,dx
    mov firstrow,ax
""", "two-point X bounds")
    edit("    ; Preserve the actual renderer result and all post-render GPRs.\n    push ax\n    push bx\n",
         "    ; Preserve the actual renderer result and all post-render GPRs.\n    push ax\n    push bx\n    push cx\n    push dx\n", "Output preserve X registers")
    edit("    mov ax,firstrow\n    mov bx,lastrow\n    call FlushRetainRows\n    jmp short TOutput_flushed\n",
         """    mov ax,firstrow
    mov bx,lastrow
    mov cx,firstcol
    mov dx,lastcol
    add dx,7
    shr cx,1
    shr cx,1
    shr cx,1
    shr dx,1
    shr dx,1
    shr dx,1
    call FlushRetainColumns
    jmp short TOutput_flushed
""", "synchronous narrow presentation")
    edit("TOutput_flushed:\n    pop bx\n    pop ax\n",
         "TOutput_flushed:\n    pop dx\n    pop cx\n    pop bx\n    pop ax\n", "Output restore X registers")
    # All geometry is clipped before cursor ownership. Convert logical rows
    # and eight-pixel columns to viewport rows and packed physical bytes.
    # The existing lease serializes interrupt-time cursor motion using tc_depth.
    # Staging (xy_copy_mode=1) still skips cursor work, exactly as before.
    edit("    sub sp,24\n    cmp enabled_flag,0\n",
         "    sub sp,26\n    cmp enabled_flag,0\n", "XY cursor token")
    edit("    call cursor_hide\nxyc_begin:\n",
         """    sub ax,ss:[bp-14]
    sub bx,ss:[bp-14]
    sub cx,ss:[bp-10]
    sub dx,ss:[bp-10]
    shl cx,1
    shl cx,1
    shl dx,1
    shl dx,1
    lea si,[bp-26]
    call cursor_begin_retain
xyc_begin:
""", "XY physical cursor footprint")
    edit("xyc_show:\n    call cursor_show\n",
         "xyc_show:\n    lea si,[bp-26]\n    call cursor_end_retain\n", "XY foreground cursor release")
    if "rr_bopen" in t or "BatchClose" in t:
        raise SystemExit("XRBATCH: unexpected deferred batch state")
    if "\n" in t.replace("\r\n", ""):
        raise SystemExit("XRBATCH: refusing bare LF")
    # XYPATCH replaced begin_retain with an unused no-op stub. Restore the
    # existing, bounded CURKEEP implementation now that callers provide the
    # actual viewport footprint; its legacy branch must really hide before
    # end_retain can show/refresh the cursor.
    cur = renderer / "EGA/TCURSOR.ASM"
    cursor = cur.read_bytes().decode("latin1")
    old = ("cursor_begin_retain proc far\r\n"
           "    ; Conservatively disable footprint-retention in the XY experiment.\r\n"
           "    pushf\r\n    mov word ptr ss:[si],0\r\n    popf\r\n    retf\r\n"
           "cursor_begin_retain endp\r\n")
    keep = importlib.machinery.SourceFileLoader(
        "xr_keep", str(HERE.parents[1] / "src/tandysw/CURKEEP.PY")).load_module()
    helpers = keep.cursor_helpers(160)
    start = helpers.index("cursor_begin_retain proc far\n")
    stop = helpers.index("cursor_begin_retain endp\n", start) + len("cursor_begin_retain endp\n")
    cursor = rr.replace_n(cursor, old, helpers[start:stop].replace("\n", "\r\n"), 1, "restore CURKEEP foreground lease")
    p.write_bytes(t.encode("latin1"))
    cur.write_bytes(cursor.encode("latin1"))
