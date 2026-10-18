"""Strict, host-only Win16 import and callback bridge slices.

Only KERNEL ordinal 91 is bound. Its register results model the task-start
return contract reported by Wine's Win16 compatibility implementation; this
does not allocate a Windows task, PSP, local heap, stack, or DLL instance data.
Unknown imports and unsupported callback instructions fail closed.
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


class GuestCallbackDispatcher:
    """Synchronously invoke a far guest routine and require a matching RETF."""

    def __init__(self, *, instruction_limit: int = 64) -> None:
        if instruction_limit <= 0:
            raise ValueError("instruction_limit must be positive")
        self.instruction_limit = instruction_limit

    def invoke(self, cpu: CPU, selector: int, offset: int) -> int:
        host_frame = (cpu.CS, cpu.IP, cpu.SP)
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
    """One-import Win16 host bridge; deliberately not a Windows subsystem."""

    def __init__(self, loaded: LoadedNE, task_registers: InitTaskRegisters | None = None) -> None:
        self.loaded = loaded
        self.task_registers = task_registers or InitTaskRegisters()
        self.calls: list[ImportTarget] = []
        self.callbacks = GuestCallbackDispatcher()

    def dispatch_import(self, cpu: CPU, selector: int, offset: int) -> bool:
        target = self.loaded.resolve_import(selector, offset)
        if not (target.module.upper() == "KERNEL" and target.kind == "ordinal" and target.ordinal == 91):
            raise UnsupportedImport(
                f"no host binding for {target.module} {target.kind} "
                f"{target.ordinal if target.kind == 'ordinal' else target.name}"
            )
        self.calls.append(target)
        # InitTask uses a startup-context return, not a plain import stub RETF.
        # Unwind the FAR CALL to its guest return IP, then push the zero word
        # specified by the compatibility implementation before resuming.
        cpu.far_return()
        self.init_task_register_return(cpu)
        cpu.push(0)
        return True

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

