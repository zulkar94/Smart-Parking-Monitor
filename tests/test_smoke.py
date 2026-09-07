"""Smoke test: verify package modules import successfully."""


def test_import() -> None:
    from app import anpr, database, parking, schemas

    assert anpr
    assert parking
    assert database
    assert schemas
