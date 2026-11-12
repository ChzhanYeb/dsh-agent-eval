"""Reproducible RNG state serialization helpers."""
from __future__ import annotations
import json
import random
from typing import Any


def _lists_to_tuples(value: Any) -> Any:
    if isinstance(value, list):
        return tuple(_lists_to_tuples(x) for x in value)
    if isinstance(value, dict):
        return {k: _lists_to_tuples(v) for k, v in value.items()}
    return value


def encode_state(rng: random.Random) -> str:
    """Serialize the complete getstate() value. JSON text is safe for episode logs."""
    return json.dumps(rng.getstate(), separators=(",", ":"))


def decode_state(encoded: str) -> tuple:
    raw = json.loads(encoded)
    value = _lists_to_tuples(raw)
    if not isinstance(value, tuple):
        raise ValueError("serialized random state must decode to a tuple")
    return value


def restore_rng(encoded: str) -> random.Random:
    rng = random.Random()
    rng.setstate(decode_state(encoded))
    return rng


def state_round_trip_ok(encoded: str) -> bool:
    """Check getstate -> serialized -> setstate equality without advancing RNG."""
    rng = restore_rng(encoded)
    return encode_state(rng) == encoded
