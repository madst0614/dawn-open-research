"""Offline ULID identities; namespace is supplied by program.yaml."""

import re
import secrets
import time

ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
KINDS = ("C", "Q", "I", "P", "E", "S", "R", "X", "ART", "REPO", "INFRA", "ENV", "PROFILE", "RUN", "BL", "PUB", "PROGRAM")
ULID_RE = re.compile(r"^[0-7][0-9A-HJKMNP-TV-Z]{25}$")


def new_id(namespace: str, kind: str) -> str:
    if kind not in KINDS:
        raise ValueError(f"unknown kind: {kind}")
    if not re.fullmatch(r"[A-Z][A-Z0-9]{1,15}", namespace):
        raise ValueError("namespace must be 2-16 uppercase alphanumeric characters")
    # ULID: 48-bit millisecond time and 80 cryptographically random bits.
    value = (int(time.time() * 1000) << 80) | secrets.randbits(80)
    encoded = "".join(ALPHABET[(value >> (5 * i)) & 31] for i in range(25, -1, -1))
    return f"{namespace}-{kind}-{encoded}"


def validate_id(value: str, namespace: str, kind: str | None = None) -> str:
    if not isinstance(value, str):
        raise ValueError("ID must be a string")
    match = re.fullmatch(r"([A-Z][A-Z0-9]{1,15})-([A-Z]+)-([0-9A-HJKMNP-TV-Z]{26})", value)
    if not match or match[1] != namespace or match[2] not in KINDS or (kind and match[2] != kind) or not ULID_RE.fullmatch(match[3]):
        raise ValueError(f"invalid {kind or 'object'} ID for namespace {namespace}: {value}")
    return match[2]
