def test_import():
    """Smoke test: verify main modules import successfully."""
    import anpr
    import parking
    import database
    import schemas
    assert anpr
    assert parking
    assert database
    assert schemas
