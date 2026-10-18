"""Fail-closed, host-only loader for the NE features used by this probe.

The loader reuses ``tools/W31CHECK/w31check.py`` to parse NE structures. It
creates private 64 KiB selector windows in a host bytearray and resolves NE
fixups to symbolic import stubs. It does not emulate Windows allocation,
callbacks, API behavior, or a complete NE loader.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

MEMORY_SIZE = 1 << 20
IMPORT_SELECTOR_BASE = 0xF000
CODE_SELECTOR_BASE = 0x1000
SELECTOR_STRIDE = 0x1000
SEGMENT_SIZE = 0x10000


class NELoadError(RuntimeError):
    """The image uses an unsupported or invalid NE loading feature."""


@dataclass(frozen=True)
class ImportTarget:
    module: str
    kind: str
    name: str | None
    ordinal: int | None


@dataclass
class LoadedNE:
    memory: bytearray
    image: Any
    segment_selectors: dict[int, int]
    import_targets: dict[tuple[int, int], ImportTarget]
    initial_cs: int
    initial_ip: int
    initial_ss: int
    initial_sp: int
    loaded_bytes: int

    def resolve_import(self, selector: int, offset: int) -> ImportTarget:
        try:
            return self.import_targets[(selector, offset)]
        except KeyError as exc:
            raise NELoadError(
                f"far call to unbound import stub {selector:04X}:{offset:04X}"
            ) from exc


class NELoader:
    """Load the bounded NE subset required by the original-entry probe."""

    def __init__(self, image: Any) -> None:
        self.image = image

    @classmethod
    def from_bytes(cls, data: bytes, source: str = "<memory>") -> "NELoader":
        # Import the canonical public parser only when parsing is requested.
        # Keeping this lazy also lets the isolated unit tests supply fake NE
        # structures without copying the analyzer or any guest binary.
        try:
            from tools.W31CHECK.w31check import NEImage
        except ImportError as exc:
            raise NELoadError(
                "run from the repository root so the public W31CHECK parser is importable"
            ) from exc
        return cls(NEImage(data, source))

    def load(self) -> LoadedNE:
        image = self.image
        memory = bytearray(MEMORY_SIZE)
        selectors: dict[int, int] = {}
        windows: dict[int, bytearray] = {}
        loaded_bytes = 0

        if len(image.segments) != image.segment_count:
            raise NELoadError("parsed segment count does not match the NE header")
        for index, segment in enumerate(image.segments, start=1):
            selector = CODE_SELECTOR_BASE + (index - 1) * SELECTOR_STRIDE
            base = selector << 4
            if selector > 0xE000 or base + SEGMENT_SIZE > MEMORY_SIZE:
                raise NELoadError(f"segment {index} has no safe selector window")
            if len(segment.data) > SEGMENT_SIZE or segment.minimum_allocation > SEGMENT_SIZE:
                raise NELoadError(f"segment {index} exceeds the 16-bit segment model")
            if len(segment.data) > segment.minimum_allocation:
                raise NELoadError(f"segment {index} file data exceeds minimum allocation")
            selectors[index] = selector
            window = bytearray(SEGMENT_SIZE)
            window[: len(segment.data)] = segment.data
            windows[index] = window
            loaded_bytes += len(segment.data)

        imports: dict[tuple[int, int], ImportTarget] = {}
        import_offsets: dict[tuple[str, str, str | int], int] = {}
        next_import_offset: dict[str, int] = {}

        def import_target(relocation: dict[str, Any]) -> tuple[int, int, ImportTarget]:
            module_ref = int(relocation["target1"])
            if not 1 <= module_ref <= len(image.modules):
                raise NELoadError(f"invalid NE module reference {module_ref}")
            module = image.modules[module_ref - 1].upper()
            target_kind = int(relocation["target_flags"]) & 0x03
            if target_kind == 1:
                kind = "ordinal"
                ordinal = int(relocation["target2"])
                key: str | int = ordinal
                name = None
            elif target_kind == 2:
                kind = "name"
                import_name_offset = int(relocation["target2"])
                try:
                    name = image.import_name_table[import_name_offset]
                except KeyError as exc:
                    raise NELoadError(
                        f"missing imported name at NE import-table offset {import_name_offset}"
                    ) from exc
                ordinal = None
                key = name
            else:
                raise NELoadError(f"relocation is not an imported function: target {target_kind}")
            identity = (module, kind, key)
            if identity not in import_offsets:
                offset = next_import_offset.get(module, 1)
                if offset > 0xFFFF:
                    raise NELoadError(f"too many import stubs for {module}")
                import_offsets[identity] = offset
                next_import_offset[module] = offset + 1
            selector = IMPORT_SELECTOR_BASE + module_ref
            offset = import_offsets[identity]
            target = ImportTarget(module, kind, name, ordinal)
            imports[(selector, offset)] = target
            return selector, offset, target

        for segment in image.segments:
            window = windows[segment.number]
            for relocation in segment.relocations:
                source_type = int(relocation["source_type"]) & 0x7F
                target_flags = int(relocation["target_flags"])
                target_kind = target_flags & 0x03
                additive = bool(target_flags & 0x04)
                width = {0: 1, 2: 2, 3: 4, 5: 2}.get(source_type)
                if width is None or not relocation.get("source_type_known", False):
                    raise NELoadError(f"unsupported NE relocation source type {source_type}")
                sites = tuple(relocation.get("chain_sites", ()))
                if not sites:
                    raise NELoadError("NE relocation has no source sites")

                target_selector: int
                target_offset: int
                if target_kind == 0:
                    target_segment = int(relocation["target1"]) & 0xFF
                    if target_segment == 0xFF:
                        movable_ordinal = int(relocation["target2"])
                        matches = [entry for entry in image.entry_points
                                   if entry.ordinal == movable_ordinal]
                        if len(matches) != 1:
                            raise NELoadError(
                                f"movable entry ordinal {movable_ordinal} is absent or ambiguous"
                            )
                        target_segment = matches[0].segment
                        movable_offset = matches[0].offset
                    else:
                        movable_offset = None
                    if target_segment not in selectors:
                        raise NELoadError(f"invalid internal segment target {target_segment}")
                    target_selector = selectors[target_segment]
                    target_offset = (
                        int(movable_offset) if movable_offset is not None
                        else int(relocation["target2"]) & 0xFFFF
                    )
                elif target_kind in (1, 2):
                    target_selector, target_offset, _ = import_target(relocation)
                else:
                    raise NELoadError("OS-specific NE fixups are not supported")

                for site in sites:
                    if site < 0 or site + width > SEGMENT_SIZE:
                        raise NELoadError(f"relocation site {site!r} is outside its segment")
                    if source_type == 0:
                        value = (target_offset + (window[site] if additive else 0)) & 0xFF
                        window[site] = value
                    elif source_type == 2:
                        value = target_selector
                        if additive:
                            value = (value + int.from_bytes(window[site : site + 2], "little")) & 0xFFFF
                        window[site : site + 2] = value.to_bytes(2, "little")
                    elif source_type == 5:
                        value = target_offset
                        if additive:
                            value = (value + int.from_bytes(window[site : site + 2], "little")) & 0xFFFF
                        window[site : site + 2] = value.to_bytes(2, "little")
                    else:  # far pointer: offset word followed by selector word
                        offset_value = target_offset
                        if additive:
                            offset_value = (
                                offset_value + int.from_bytes(window[site : site + 2], "little")
                            ) & 0xFFFF
                        window[site : site + 2] = offset_value.to_bytes(2, "little")
                        window[site + 2 : site + 4] = target_selector.to_bytes(2, "little")

        for segment_number, window in windows.items():
            base = selectors[segment_number] << 4
            memory[base : base + SEGMENT_SIZE] = window

        if image.initial_cs not in selectors or image.initial_ss not in selectors:
            raise NELoadError("NE initial CS or SS references an absent segment")
        return LoadedNE(
            memory=memory,
            image=image,
            segment_selectors=selectors,
            import_targets=imports,
            initial_cs=selectors[image.initial_cs],
            initial_ip=image.initial_ip,
            initial_ss=selectors[image.initial_ss],
            initial_sp=image.initial_sp,
            loaded_bytes=loaded_bytes,
        )

