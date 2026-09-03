from __future__ import annotations

import hashlib
import hmac

import pytest
from fastapi import HTTPException

from onboarding_routes import _password_hash, _validate_profile


def test_passwords_are_salted_pbkdf2_hashes():
    password = "correct horse battery staple"
    stored = _password_hash(password)
    algorithm, salt, digest = stored.split("$", 2)
    assert algorithm == "pbkdf2_sha256"
    assert password not in stored
    expected = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), bytes.fromhex(salt), 240_000
    ).hex()
    assert hmac.compare_digest(expected, digest)


def test_password_hashes_use_random_salts():
    password = "a sufficiently long password"
    assert _password_hash(password) != _password_hash(password)


def test_profile_validation_accepts_arbitrary_sequence_lengths():
    start, end = _validate_profile(
        "2026-09-01",
        "2027-06-20",
        "America/New_York",
        ["A", "B", "C", "D", "E", "F"],
        6,
    )
    assert start.isoformat() == "2026-09-01"
    assert end.isoformat() == "2027-06-20"


def test_profile_validation_rejects_bad_starting_sequence_day():
    with pytest.raises(HTTPException):
        _validate_profile(
            "2026-09-01", "2027-06-20", "America/New_York", ["A", "B"], 3
        )
