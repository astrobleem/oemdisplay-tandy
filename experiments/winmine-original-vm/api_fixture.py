"""First-party 8086 fixture for one Win3.0 API round-trip and USER callback.

The fixture issues name-based imports for GetVersion, MakeProcInstance, and
EnumWindows. Its synthetic USER window list is supplied by the host, while
the callback itself is ordinary guest machine code executed by ``CPU.step``.
No Windows image, ROM, original application, or emulator is involved.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

from cpu_subset import CPU, UnsupportedOpcode
from ne_loader import ImportTarget, LoadedNE, NELoader
from win16_host import CallbackInvocation, Win16Host


CODE_SELECTOR = 0x1000
INSTANCE_SELECTOR = 0x2000
CALLER_DATA_SELECTOR = 0x3000
STACK_SELECTOR = 0x4000
ENTRY_OFFSET = 0x0100
CALLBACK_OFFSET = 0x0200
INSTANCE_HANDLE = 0x0042
LPARAM = 0xABCD5678
WINDOWS = (0x1111, 0x2222, 0x3333)

VERSION_WORD_OFFSET = 0x0120
PROC_INSTANCE_OFFSET = 0x0122
PROC_INSTANCE_SELECTOR_OFFSET = 0x0124
ENUM_RESULT_OFFSET = 0x0126
CALLBACK_WINDOW_OFFSET = 0x0100
CALLBACK_LPARAM_LOW_OFFSET = 0x0102
CALLBACK_LPARAM_HIGH_OFFSET = 0x0104


@dataclass(frozen=True)
class FixtureResult:
    """Observable registers, API calls, and callback side effects."""

    version_word: int
    proc_instance: tuple[int, int]
    enum_result: int
    api_calls: tuple[ImportTarget, ...]
    callback_invocations: tuple[CallbackInvocation, ...]
    last_callback_window: int
    callback_lparam: int
    caller_ds_restored: bool
    final_stack_pointer: int
    instructions: int


def _far_call_import(
    module_ref: int,
    import_name_offset: int,
    source_offset: int,
) -> tuple[bytes, dict[str, object]]:
    """Return a placeholder CALL FAR and its synthetic NE name relocation."""

    code = b"\x9a\0\0\0\0"
    relocation = {
        "source_type": 3,
        "target_flags": 2,
        "source_offset": source_offset,
        "target1": module_ref,
        "target2": import_name_offset,
        "source_width": 4,
        "source_type_known": True,
        "chain_sites": (source_offset,),
    }
    return code, relocation


def _entry_code() -> tuple[bytes, tuple[dict[str, object], ...]]:
    code = bytearray()
    relocations = []

    def import_call(module_ref: int, import_name_offset: int) -> None:
        source_offset = len(code) + 1  # Relocation points at CALL FAR's m16:16 operand.
        call, relocation = _far_call_import(module_ref, import_name_offset, source_offset)
        code.extend(call)
        relocations.append(relocation)

    import_call(1, 1)                          # KERNEL!GetVersion()
    code += bytes.fromhex("89 06 20 01")          # mov [0120],ax

    # MakeProcInstance((FARPROC)1000:0200, 0042h). Win16 Pascal pushes
    # arguments left-to-right; the final hInstance argument is pushed last.
    code += bytes.fromhex("B8 00 10 50")          # callback selector
    code += bytes.fromhex("B8 00 02 50")          # callback offset
    code += bytes.fromhex("B8 42 00 50")          # hInstance
    import_call(1, 2)                          # KERNEL!MakeProcInstance
    code += bytes.fromhex("89 06 22 01")          # save FARPROC offset (AX)
    code += bytes.fromhex("89 16 24 01")          # save FARPROC selector (DX)

    # EnumWindows(procInstance, 0xABCD5678). Each 32-bit Pascal argument is
    # pushed high-word then low-word, making its low word nearest the return.
    code += bytes.fromhex("52 50")                # push DX:AX as FARPROC
    code += bytes.fromhex("B8 CD AB 50")          # LPARAM high word
    code += bytes.fromhex("B8 78 56 50")          # LPARAM low word
    import_call(2, 3)                          # USER!EnumWindows
    code += bytes.fromhex("89 06 26 01")          # save EnumWindows BOOL
    code += b"\xcd\xff"                          # synthetic runner stop
    return bytes(code), tuple(relocations)


def _callback_code(*, return_nonzero: bool = True) -> bytes:
    # BOOL FAR PASCAL EnumProc(HWND hWnd, LPARAM lParam). Read the arguments
    # from their documented BP offsets, store them in instance DS, return TRUE,
    # and let RETF 6 perform the Pascal callee cleanup.
    code = (
        "55 "              # push bp
        "89 E5 "           # mov bp,sp
        "8B 46 0A "        # mov ax,[bp+10] (hWnd)
        "89 06 00 01 "     # mov [ds:0100],ax
        "8B 4E 06 "        # mov cx,[bp+6] (LPARAM low)
        "89 0E 02 01 "     # mov [ds:0102],cx
        "8B 56 08 "        # mov dx,[bp+8] (LPARAM high)
        "89 16 04 01 "     # mov [ds:0104],dx
        + ("B8 01 00 " if return_nonzero else "B8 00 00 ")
        + "5D "            # pop bp
        + "CA 06 00"       # retf 6
    )
    return bytes.fromhex(code)


def _build_loaded(*, callback_returns_nonzero: bool = True) -> LoadedNE:
    entry, relocations = _entry_code()
    relocations = tuple(
        {
            **relocation,
            "source_offset": int(relocation["source_offset"]) + ENTRY_OFFSET,
            "chain_sites": tuple(int(site) + ENTRY_OFFSET
                                  for site in relocation["chain_sites"]),
        }
        for relocation in relocations
    )
    code = bytearray(CALLBACK_OFFSET + 0x40)
    code[ENTRY_OFFSET:ENTRY_OFFSET + len(entry)] = entry
    callback = _callback_code(return_nonzero=callback_returns_nonzero)
    code[CALLBACK_OFFSET:CALLBACK_OFFSET + len(callback)] = callback

    # Feed the first-party byte fixture through the same bounded NE relocation
    # path as a parsed program. The machine-code imports stay name-based and the
    # host still supplies only synthetic USER windows and API behavior.
    image = SimpleNamespace(
        segment_count=4,
        segments=(
            SimpleNamespace(number=1, data=bytes(code), minimum_allocation=len(code),
                            relocations=relocations),
            SimpleNamespace(number=2, data=b"\0" * 0x200, minimum_allocation=0x200,
                            relocations=()),
            SimpleNamespace(number=3, data=b"\0" * 0x200, minimum_allocation=0x200,
                            relocations=()),
            SimpleNamespace(number=4, data=b"", minimum_allocation=0x1000,
                            relocations=()),
        ),
        modules=("KERNEL", "USER"),
        import_name_table={1: "GetVersion", 2: "MakeProcInstance", 3: "EnumWindows"},
        entry_points=(),
        initial_cs=1,
        initial_ip=ENTRY_OFFSET,
        initial_ss=4,
        initial_sp=0x0100,
    )
    return NELoader(image).load()


def run_api_callback_fixture(
    *,
    instruction_limit: int = 128,
    callback_returns_nonzero: bool = True,
) -> FixtureResult:
    """Run the 8086 guest fixture through API return and three callbacks.

    The returned state proves only that this first-party byte fixture executed
    the documented stack shapes through the deliberately bounded host bridge.
    The HWND values are synthetic and do not come from a Windows desktop.
    """

    if instruction_limit <= 0:
        raise ValueError("instruction_limit must be positive")
    loaded = _build_loaded(callback_returns_nonzero=callback_returns_nonzero)
    cpu = CPU(memory=loaded.memory)
    cpu.CS, cpu.IP = loaded.initial_cs, loaded.initial_ip
    cpu.SS, cpu.SP = loaded.initial_ss, loaded.initial_sp
    cpu.DS = CALLER_DATA_SELECTOR
    host = Win16Host(
        loaded,
        windows=WINDOWS,
        instance_data_segments={INSTANCE_HANDLE: INSTANCE_SELECTOR},
    )

    initial_ds = cpu.DS
    for instructions in range(1, instruction_limit + 1):
        try:
            event = cpu.step()
        except UnsupportedOpcode:
            raise
        if event[0] == "far_call":
            _, target_cs, target_ip = event
            host.dispatch_import(cpu, target_cs, target_ip)
        elif event[0] == "host_interrupt":
            if event[1] != 0xFF:
                raise RuntimeError(f"unexpected fixture interrupt {event[1]:02X}")
            break
        elif event[0] not in ("instruction", "far_return"):
            raise RuntimeError(f"unsupported fixture control event {event[0]}")
    else:
        raise RuntimeError(f"fixture did not stop within {instruction_limit} instructions")

    read = cpu.read16
    version_word = read(CALLER_DATA_SELECTOR, VERSION_WORD_OFFSET)
    proc_instance = (
        read(CALLER_DATA_SELECTOR, PROC_INSTANCE_SELECTOR_OFFSET),
        read(CALLER_DATA_SELECTOR, PROC_INSTANCE_OFFSET),
    )
    enum_result = read(CALLER_DATA_SELECTOR, ENUM_RESULT_OFFSET)
    callback_lparam = (
        read(INSTANCE_SELECTOR, CALLBACK_LPARAM_HIGH_OFFSET) << 16
    ) | read(INSTANCE_SELECTOR, CALLBACK_LPARAM_LOW_OFFSET)
    return FixtureResult(
        version_word=version_word,
        proc_instance=proc_instance,
        enum_result=enum_result,
        api_calls=tuple(host.calls),
        callback_invocations=tuple(host.callback_invocations),
        last_callback_window=read(INSTANCE_SELECTOR, CALLBACK_WINDOW_OFFSET),
        callback_lparam=callback_lparam,
        caller_ds_restored=cpu.DS == initial_ds,
        final_stack_pointer=cpu.SP,
        instructions=instructions + host.callback_guest_instructions,
    )


if __name__ == "__main__":
    result = run_api_callback_fixture()
    print(f"GetVersion word: {result.version_word:04X}")
    print(f"MakeProcInstance token: {result.proc_instance[0]:04X}:{result.proc_instance[1]:04X}")
    print(f"EnumWindows returned: {result.enum_result}")
    print(f"Guest callbacks: {len(result.callback_invocations)}")
    print(f"Last guest callback HWND: {result.last_callback_window:04X}")
    print(f"Guest callback LPARAM: {result.callback_lparam:08X}")
    print(f"Caller DS restored: {result.caller_ds_restored}")
    print(f"8086 instructions: {result.instructions}")
