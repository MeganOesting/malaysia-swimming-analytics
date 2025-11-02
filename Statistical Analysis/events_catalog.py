# -*- coding: utf-8 -*-
from typing import Tuple

# Canonical finite set of events (as strings used across the project)
CANONICAL_EVENTS = {
    '50 Free', '100 Free', '200 Free', '400 Free', '800 Free', '1500 Free',
    '100 Back', '200 Back', '100 Breast', '200 Breast', '100 Fly', '200 Fly',
    '200 IM', '400 IM'
}

# Optional mapping for common aliases → canonical
ALIASES = {
    '50 freestyle': '50 Free',
    '100 freestyle': '100 Free',
    '200 freestyle': '200 Free',
    '400 freestyle': '400 Free',
    '800 freestyle': '800 Free',
    '1500 freestyle': '1500 Free',
    '100 backstroke': '100 Back',
    '200 backstroke': '200 Back',
    '100 breaststroke': '100 Breast',
    '200 breaststroke': '200 Breast',
    '100 butterfly': '100 Fly',
    '200 butterfly': '200 Fly',
    '200 individual medley': '200 IM',
    '400 individual medley': '400 IM',
}


def normalize_event(event: str) -> Tuple[bool, str]:
    """Return (is_valid, canonical_event). Reject or normalize to a canonical string."""
    if not event:
        return False, ''
    s = event.strip()
    if s in CANONICAL_EVENTS:
        return True, s
    low = s.lower()
    if low in ALIASES:
        return True, ALIASES[low]
    # Try basic normalization: title-case common forms
    s_try = ' '.join(w.capitalize() for w in low.split())
    if s_try in CANONICAL_EVENTS:
        return True, s_try
    return False, s  # not canonical



