# 0002 — `Glasses` as a Protocol, not an ABC

**Status:** Accepted · **Date:** 2026-05-19

## Context

Compass needs a hardware abstraction so the same pipeline runs against the mock today, a used Frame later, and whatever device wins (Z100, Halo, Mentra Live + Even Realities G1) next. The Python toolbox offers two ways to express this kind of polymorphism: abstract base classes (`abc.ABC`) and structural typing (`typing.Protocol`).

The choice matters because external SDKs — Brilliant's community `frame-msg` / `frame-ble`, Mentra's TypeScript bridge, a future Halo SDK, whatever Vuzix ships — won't inherit from our ABC. They'll just have methods.

## Decision

`Glasses` is a `typing.Protocol`, decorated `@runtime_checkable`. The methods are: `connect`, `wait_for_trigger`, `capture_image`, `show_text`, `close`.

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class Glasses(Protocol):
    def connect(self) -> None: ...
    def wait_for_trigger(self) -> bool: ...
    def capture_image(self) -> bytes: ...
    def show_text(self, line1: str, line2: str = "", *, color: str = "green") -> None: ...
    def close(self) -> None: ...
```

Drivers (mock, frame, future halo/z100/mentra) just implement the methods. No inheritance, no registration.

## Consequences

**Good:**
- Third-party SDKs drop in without a wrapper class. If `frame-msg`'s `Frame` object already has the right methods (it nearly does), we can use it directly.
- Tests use plain duck-typed fakes without `class FakeGlasses(Glasses): ...` ceremony.
- `isinstance(x, Glasses)` still works at runtime for the cases that need it (CLI sanity check, plugin loader).
- The protocol is documentation: the five methods are the entire hardware contract. Anything else (camera resolution, BLE chunk size, display color depth) is the driver's private business.

**Bad:**
- No shared default behavior. If two drivers need to log to the same place on every call, we duplicate the logging or factor it out into a free function. Acceptable cost for the abstraction win.
- Static type checkers can't catch a missing method until the driver is *used*. Mitigated by smoke tests that instantiate every driver.

## Alternatives considered

- **`abc.ABC` with required abstract methods.** Rejected: forces external SDKs into a wrapper class even when their interface already matches. Adds ceremony without adding safety.
- **A registry pattern (`@register_driver`).** Rejected: solves a plugin problem we don't have. We pick the driver at config-load time, not at runtime discovery.
- **Just duck-type without `Protocol`.** Rejected: loses the documentation value and the `isinstance` check. `Protocol` is the cheapest formalization of what we'd do informally anyway.
