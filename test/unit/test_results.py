from tuxrun.results import Results


def test_returns_0_by_default():
    results = Results()
    assert results.ret() == 0


def test_returns_0_with_no_failures():
    results = Results()
    results.parse('{ "lvl": "results", "msg": {"case": "test1", "result": "pass"}}')
    results.parse('{ "lvl": "results", "msg": {"case": "test2", "result": "pass"}}')
    assert results.ret() == 0


def test_returns_1_on_failure():
    results = Results()
    results.parse('{ "lvl": "results", "msg": {"case": "test1", "result": "pass"}}')
    results.parse('{ "lvl": "results", "msg": {"case": "test2", "result": "fail"}}')
    assert results.ret() == 1
