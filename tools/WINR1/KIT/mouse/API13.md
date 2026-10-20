# `WHEELREADDELTAAGE` (ordinal 13)

This candidate adds a parallel API and does not change v1 ordinals 10-12 or `WheelApiVersion` (`0100h`). It exports the exact uppercase name `WHEELREADDELTAAGE` at ordinal 13.

Call as a far procedure. On return, AX contains the signed wheel delta and DX contains its age in BIOS ticks. AX is zero when no delta is available. DX is `FFFFh` when the queue is empty/inactive, the current BDA tick count is outside `0..001800AFh`, the clock moved backwards relative to the queued event, or the computed age is `FFFFh` or greater. A queued delta is still returned when its age is unknown.

The procedure preserves BX, CX, SI, DI, BP, DS, ES, IF and DF; AX and DX are outputs. It atomically snapshots queue tail, the corresponding timestamp, and current BIOS ticks with interrupts disabled before consuming the delta. The timestamp table is a parallel 32-slot DWORD ring. IRQ4 stamps a slot only when `dec_feed` advances the queue head, before callback dispatch or consumer exposure. A full queue drops newest and leaves existing slot timestamps untouched. The implementation does not hook IRQ0 or call DOS/USER from the interrupt path.

The caller contract assumes that the current BIOS tick count is from the same day and has advanced monotonically since the event timestamp. A backwards tick sample or an out-of-range BDA count is reported as unknown (`FFFFh`). The API cannot identify every cross-midnight alias: for example, an event stamped at tick 1 and a current tick of 5 on the next day would appear to have age 4. Callers that can span a date boundary must apply a date/epoch guard; the bridge supplies that guard. This API reports the delta age at dequeue time, not hardware arrival time or callback completion time.
