"""Strict, host-only Win16 import and callback bridge slices.

The model binds a small explicit set of Win16 APIs and executes bounded guest
callbacks. It is not a Windows subsystem: the fixture supplies window handles,
instance data selectors, and task-start context, and the MakeProcInstance
result is a host-resolved token rather than generated thunk code. Unknown
imports and unsupported callback instructions fail closed.
"""

from __future__ import annotations

from dataclasses import dataclass

from cpu_subset import CPU, UnsupportedOpcode
from ne_loader import ImportTarget, LoadedNE


class UnsupportedImport(RuntimeError):
    """Raised for an imported function without an explicit host binding."""


class CallbackError(RuntimeError):
    """Raised when a far guest callback cannot return to its host frame."""


@dataclass(frozen=True)
class ProcInstance:
    """A host-resolved Win16 procedure-instance token.

    Windows' MakeProcInstance creates a prolog that binds an instance data
    segment. This bounded host model records that binding and dispatches the
    guest callback with DS set accordingly; it does not emit thunk bytes.
    """

    callback_selector: int
    callback_offset: int
    instance_selector: int


@dataclass(frozen=True)
class CallbackInvocation:
    """One completed callback from the synthetic USER window list."""

    window: int
    lparam: int
    returned_nonzero: bool
    instance_selector: int


@dataclass(frozen=True)
class InitTaskRegisters:
    """Host-provided values for the small InitTask register-return slice.

    These are launch-context inputs, not values allocated or discovered by a
    Windows-compatible memory manager.
    """

    stack_limit: int = 0x2000
    show_command: int = 1
    previous_instance: int = 0
    instance: int = 1
    psp_segment: int = 0x3000
    command_tail_offset: int = 0x0080

    def __post_init__(self) -> None:
        for name, value in vars(self).items():
            if not 0 <= value <= 0xFFFF:
                raise ValueError(f"{name} must be a 16-bit unsigned value")


@dataclass(frozen=True)
class Dos3CallRecord:
    """One bounded DOS3Call invocation using a synthetic DOS vector table."""

    request_ax: int
    interrupt_number: int
    action: str
    vector_before: tuple[int, int] | None
    vector_after: tuple[int, int]
    handler_sp: int
    returned_sp: int


@dataclass(frozen=True)
class SyntheticDosVersion:
    """Explicit DOS 21h/AH=30h return values for host-only startup probes."""

    major: int
    minor: int
    oem_id: int = 0
    serial24: int = 0

    def __post_init__(self) -> None:
        if any(not 0 <= value <= 0xFF for value in (self.major, self.minor, self.oem_id)):
            raise ValueError("synthetic DOS major/minor/OEM values must be 8-bit unsigned values")
        if not 0 <= self.serial24 <= 0xFFFFFF:
            raise ValueError("synthetic DOS serial number must be a 24-bit unsigned value")


@dataclass(frozen=True)
class DosVersionCallRecord:
    request_ax: int
    major: int
    minor: int
    oem_id: int
    serial24: int
    handler_sp: int
    returned_sp: int


class GuestCallbackDispatcher:
    """Synchronously invoke a far guest routine and require a matching RETF."""

    def __init__(self, *, instruction_limit: int = 64) -> None:
        if instruction_limit <= 0:
            raise ValueError("instruction_limit must be positive")
        self.instruction_limit = instruction_limit

    def invoke(
        self,
        cpu: CPU,
        selector: int,
        offset: int,
        *,
        argument_words_push_order: tuple[int, ...] = (),
    ) -> int:
        host_frame = (cpu.CS, cpu.IP, cpu.SP)
        for word in argument_words_push_order:
            if not 0 <= word <= 0xFFFF:
                raise ValueError("callback argument words must be 16-bit unsigned values")
            cpu.push(word)
        cpu.call_far(selector, offset)
        for steps in range(1, self.instruction_limit + 1):
            if (cpu.CS, cpu.IP) == host_frame[:2]:
                if cpu.SP != host_frame[2]:
                    raise CallbackError(
                        f"callback returned with SP={cpu.SP:04X}, expected {host_frame[2]:04X}"
                    )
                return steps - 1
            try:
                event = cpu.step()
            except UnsupportedOpcode as exc:
                raise CallbackError(f"unsupported callback instruction: {exc}") from exc
            if event[0] != "instruction" and event[0] != "far_return":
                raise CallbackError(f"callback used unsupported control event {event[0]}")
        raise CallbackError(
            f"callback did not return to {host_frame[0]:04X}:{host_frame[1]:04X} "
            f"within {self.instruction_limit} instructions"
        )


class Win16Host:
    """Small explicit Win16 API bridge; deliberately not a Windows subsystem."""

    def __init__(
        self,
        loaded: LoadedNE,
        task_registers: InitTaskRegisters | None = None,
        *,
        windows: tuple[int, ...] = (),
        instance_data_segments: dict[int, int] | None = None,
        version_word: int = 0x0003,
        dos_interrupt_vectors: dict[int, tuple[int, int]] | None = None,
        dos_version: SyntheticDosVersion | None = None,
    ) -> None:
        self.loaded = loaded
        self.task_registers = task_registers or InitTaskRegisters()
        self.windows = tuple(windows)
        if any(not 0 <= hwnd <= 0xFFFF for hwnd in self.windows):
            raise ValueError("synthetic HWND values must be 16-bit unsigned values")
        self.instance_data_segments = dict(instance_data_segments or {})
        if any(not 0 <= handle <= 0xFFFF or not 0 <= selector <= 0xFFFF
               for handle, selector in self.instance_data_segments.items()):
            raise ValueError("instance handles and selectors must be 16-bit unsigned values")
        if not 0 <= version_word <= 0xFFFF:
            raise ValueError("version_word must be a 16-bit unsigned value")
        self.version_word = version_word
        if dos_version is not None and not isinstance(dos_version, SyntheticDosVersion):
            raise ValueError("dos_version must be an explicit SyntheticDosVersion")
        self.dos_version = dos_version
        self.dos_interrupt_vectors = dict(dos_interrupt_vectors or {})
        for interrupt_number, pointer in self.dos_interrupt_vectors.items():
            if not 0 <= interrupt_number <= 0xFF:
                raise ValueError("synthetic interrupt numbers must be 8-bit unsigned values")
            if (not isinstance(pointer, tuple) or len(pointer) != 2
                    or any(not 0 <= value <= 0xFFFF for value in pointer)):
                raise ValueError(
                    "synthetic DOS vectors must be (segment, offset) 16-bit tuples"
                )
        self.calls: list[ImportTarget] = []
        self.dos3call_records: list[Dos3CallRecord] = []
        self.dos_version_call_records: list[DosVersionCallRecord] = []
        self.callbacks = GuestCallbackDispatcher()
        self.proc_instances: dict[tuple[int, int], ProcInstance] = {}
        self.callback_invocations: list[CallbackInvocation] = []
        self.callback_guest_instructions = 0
        self._next_proc_instance_offset = 1

    def dispatch_import(self, cpu: CPU, selector: int, offset: int) -> bool:
        target = self.loaded.resolve_import(selector, offset)
        module = target.module.upper()
        name = target.name.upper() if target.kind == "name" and target.name else ""

        if module == "KERNEL" and target.kind == "ordinal" and target.ordinal == 91:
            self.calls.append(target)
            # InitTask uses a startup-context return, not a plain import stub RETF.
            # Unwind the FAR CALL to its guest return IP, then push the zero word
            # specified by the compatibility implementation before resuming.
            cpu.far_return()
            self.init_task_register_return(cpu)
            cpu.push(0)
            return True
        if module == "KERNEL" and target.kind == "ordinal" and target.ordinal == 102:
            if cpu.AX == 0x3000:
                self.dos_version_call_records.append(self._dos3call_get_version(cpu))
            elif cpu.AX in (0x3500, 0x2500):
                record = self._dos3call_vector(cpu)
                self.dos3call_records.append(record)
            else:
                raise UnsupportedImport(
                    "DOS3Call bounded host model supports AX=3000h, 3500h, or 2500h; "
                    f"got {cpu.AX:04X}h"
                )
            self.calls.append(target)
            return True
        if module == "KERNEL" and target.kind == "name" and name == "GETVERSION":
            self.calls.append(target)
            cpu.far_return()
            cpu.AX = self.version_word
            return True
        if module == "KERNEL" and target.kind == "name" and name == "MAKEPROCINSTANCE":
            self._make_proc_instance(cpu)
            self.calls.append(target)
            return True
        if module == "USER" and target.kind == "name" and name == "ENUMWINDOWS":
            self._enum_windows(cpu)
            self.calls.append(target)
            return True
        else:
            raise UnsupportedImport(
                f"no host binding for {target.module} {target.kind} "
                f"{target.ordinal if target.kind == 'ordinal' else target.name}"
            )

    def _dos3call_vector(self, cpu: CPU) -> Dos3CallRecord:
        """Model DOS3Call get/set-vector calls for INT 00h only."""
        if cpu.AX not in (0x3500, 0x2500):
            raise UnsupportedImport(
                "DOS3Call bounded host model supports AX=3500h or 2500h only; "
                f"got {cpu.AX:04X}h"
            )
        interrupt_number = cpu.AX & 0xFF
        if interrupt_number != 0:
            raise UnsupportedImport(
                "DOS3Call bounded host model supports interrupt 00h only; "
                f"got {interrupt_number:02X}h"
            )

        action = "get" if cpu.AX == 0x3500 else "set"
        vector_before = self.dos_interrupt_vectors.get(interrupt_number)
        if action == "get" and vector_before is None:
            raise UnsupportedImport(
                "DOS3Call has no synthetic vector for interrupt 00h"
            )
        vector_after = vector_before if action == "get" else (cpu.DS, cpu.DX)
        assert vector_after is not None

        request_ax = cpu.AX
        handler_sp = cpu.SP
        # DOS3Call is FAR PASCAL with no stack parameters. The DOS request and
        # its documented inputs/outputs are carried in CPU registers.
        cpu.far_return()
        if action == "get":
            cpu.ES, cpu.BX = vector_after
        else:
            self.dos_interrupt_vectors[interrupt_number] = vector_after
        return Dos3CallRecord(
            request_ax=request_ax,
            interrupt_number=interrupt_number,
            action=action,
            vector_before=vector_before,
            vector_after=vector_after,
            handler_sp=handler_sp,
            returned_sp=cpu.SP,
        )

    def _dos3call_get_version(self, cpu: CPU) -> DosVersionCallRecord:
        """Model only DOS3Call(INT 21h/AH=30h) from an explicit fixture value."""
        if self.dos_version is None:
            raise UnsupportedImport("DOS3Call has no explicit synthetic DOS version")

        values = self.dos_version
        handler_sp = cpu.SP
        cpu.far_return()
        cpu.AX = (values.minor << 8) | values.major
        cpu.BX = (values.oem_id << 8) | ((values.serial24 >> 16) & 0xFF)
        cpu.CX = values.serial24 & 0xFFFF
        return DosVersionCallRecord(
            request_ax=0x3000,
            major=values.major,
            minor=values.minor,
            oem_id=values.oem_id,
            serial24=values.serial24,
            handler_sp=handler_sp,
            returned_sp=cpu.SP,
        )

    @staticmethod
    def _stack_word(cpu: CPU, byte_offset: int) -> int:
        return cpu.read16(cpu.SS, (cpu.SP + byte_offset) & 0xFFFF)

    def _make_proc_instance(self, cpu: CPU) -> None:
        # Win16 Pascal order: the last declared argument, hInstance, is on top.
        instance_handle = self._stack_word(cpu, 4)
        callback_offset = self._stack_word(cpu, 6)
        callback_selector = self._stack_word(cpu, 8)
        try:
            instance_selector = self.instance_data_segments[instance_handle]
        except KeyError as exc:
            raise UnsupportedImport(
                f"MakeProcInstance has no instance-data binding for {instance_handle:04X}"
            ) from exc
        if callback_selector not in self.loaded.segment_selectors.values():
            raise UnsupportedImport(
                f"MakeProcInstance callback selector {callback_selector:04X} is not loaded"
            )
        token = (0xE000, self._next_proc_instance_offset)
        self._next_proc_instance_offset += 1
        if self._next_proc_instance_offset > 0xFFFF:
            raise UnsupportedImport("host procedure-instance token space is exhausted")
        self.proc_instances[token] = ProcInstance(
            callback_selector=callback_selector,
            callback_offset=callback_offset,
            instance_selector=instance_selector,
        )
        cpu.far_return(argument_bytes=6)
        # Win16 FARPROC return convention: DX:AX is selector:offset.
        cpu.DX, cpu.AX = token

    def _enum_windows(self, cpu: CPU) -> None:
        # EnumWindows(FARPROC callback, LPARAM lParam); Pascal pushes callback
        # first, then lParam, leaving lParam's low word at the top of arguments.
        lparam_low = self._stack_word(cpu, 4)
        lparam_high = self._stack_word(cpu, 6)
        token_offset = self._stack_word(cpu, 8)
        token_selector = self._stack_word(cpu, 10)
        try:
            proc = self.proc_instances[(token_selector, token_offset)]
        except KeyError as exc:
            raise UnsupportedImport(
                f"EnumWindows received an unknown procedure-instance token "
                f"{token_selector:04X}:{token_offset:04X}"
            ) from exc

        lparam = (lparam_high << 16) | lparam_low
        returned_nonzero = True
        for hwnd in self.windows:
            caller_ds = cpu.DS
            cpu.DS = proc.instance_selector
            try:
                callback_steps = self.callbacks.invoke(
                    cpu,
                    proc.callback_selector,
                    proc.callback_offset,
                    # Physical push sequence for BOOL FAR PASCAL callback
                    # (HWND hWnd, LPARAM lParam): hWnd, high LPARAM, low LPARAM.
                    argument_words_push_order=(hwnd, lparam_high, lparam_low),
                )
                self.callback_guest_instructions += callback_steps
            finally:
                cpu.DS = caller_ds
            returned_nonzero = cpu.AX != 0
            self.callback_invocations.append(
                CallbackInvocation(hwnd, lparam, returned_nonzero, proc.instance_selector)
            )
            if not returned_nonzero:
                break

        cpu.far_return(argument_bytes=8)
        cpu.AX = int(returned_nonzero)

    def init_task_register_return(self, cpu: CPU) -> None:
        """Apply the modeled InitTask register outputs; allocation remains out of scope."""
        values = self.task_registers
        cpu.AX = 1
        cpu.CX = values.stack_limit
        cpu.DX = values.show_command
        cpu.SI = values.previous_instance
        cpu.DI = values.instance
        cpu.ES = values.psp_segment
        cpu.BX = values.command_tail_offset

    def call_guest_callback(self, cpu: CPU, selector: int, offset: int) -> int:
        return self.callbacks.invoke(cpu, selector, offset)
