"""Sort / index-assignment rules for controls, scroll hotspots, easy-switch slots."""

from __future__ import annotations

from .slots import ButtonSlot, ScrollSlot, EasySwitchSlot, THUMBWHEEL_CID


_SCROLL_KIND_ORDER = {"scrollwheel": 0, "thumbwheel": 1, "pointer": 2}


def sort_buttons(buttons: list[ButtonSlot]) -> list[ButtonSlot]:
    """Sort buttons by CID ascending; synthetic thumb wheel (0x0000) appended last.

    For the MX Master line this yields Middle / Back / Forward / Gesture /
    Shift / Thumb — identical to the shipped descriptor ordering, so
    position-based profile persistence keeps working.
    """
    def key(button: ButtonSlot) -> tuple[int, int]:
        if button.cid == THUMBWHEEL_CID:
            return (1, 0)
        return (0, button.cid)
    return sorted(buttons, key=key)


def sort_scroll(scrolls: list[ScrollSlot]) -> list[ScrollSlot]:
    """Sort scroll slots by canonical kind order; drops unknown kinds.

    The app's PointScrollPage looks hotspots up by `kind`, so ordering
    here is cosmetic — but it matches the shipped order
    (scrollwheel / thumbwheel / pointer) so golden-file diffs stay
    stable.
    """
    return sorted(
        (scroll for scroll in scrolls if scroll.kind in _SCROLL_KIND_ORDER),
        key=lambda scroll: _SCROLL_KIND_ORDER[scroll.kind],
    )


def sort_easyswitch(slots: list[EasySwitchSlot]) -> list[EasySwitchSlot]:
    """Sort easy-switch slots by 1-based index; keeps only the first three."""
    ordered = sorted(slots, key=lambda slot: slot.index)
    return ordered[:3]
