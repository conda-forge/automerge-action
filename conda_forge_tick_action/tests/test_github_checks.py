from ..automerge import _check_github_checks


def test_check_github_checks_nochecks():
    stat = _check_github_checks([])
    assert stat is None


def test_check_github_checks_ignores_self():
    checks = [
        {
            'name': 'regro-cf-autotick-bot-action',
            'status': 'blah',
            'conclusion': 'blah',
        },
    ]
    stat = _check_github_checks(checks)
    assert stat is None


def test_check_github_checks_all_pending():
    checks = [
        {
            'name': 'c1',
            'status': 'blah',
            'conclusion': 'blah',
        },
        {
            'name': 'c2',
            'status': 'blah',
            'conclusion': 'blah',
        },
    ]
    stat = _check_github_checks(checks)
    assert not stat


def test_check_github_checks_all_fail():
    checks = [
        {
            'name': 'c1',
            'status': 'completed',
            'conclusion': 'error',
        },
        {
            'name': 'c2',
            'status': 'completed',
            'conclusion': 'failure',
        },
    ]
    stat = _check_github_checks(checks)
    assert not stat


def test_check_github_checks_all_success():
    checks = [
        {
            'name': 'c1',
            'status': 'completed',
            'conclusion': 'success',
        },
        {
            'name': 'c2',
            'status': 'completed',
            'conclusion': 'success',
        },
    ]
    stat = _check_github_checks(checks)
    assert stat


def test_check_github_checks_success_plus_pending():
    checks = [
        {
            'name': 'c1',
            'status': 'blah',
            'conclusion': 'success',
        },
        {
            'name': 'c2',
            'status': 'completed',
            'conclusion': 'success',
        },
    ]
    stat = _check_github_checks(checks)
    assert not stat


def test_check_github_checks_success_plus_fail():
    checks = [
        {
            'name': 'c1',
            'status': 'completed',
            'conclusion': 'error',
        },
        {
            'name': 'c2',
            'status': 'completed',
            'conclusion': 'failure',
        },
        {
            'name': 'c3',
            'status': 'completed',
            'conclusion': 'success',
        },
    ]
    stat = _check_github_checks(checks)
    assert not stat


def test_check_github_checks_pending_plus_fail():
    checks = [
        {
            'name': 'c1',
            'status': 'completed',
            'conclusion': 'error',
        },
        {
            'name': 'c2',
            'status': 'completed',
            'conclusion': 'failure',
        },
        {
            'name': 'c3',
            'status': 'blah',
            'conclusion': 'success',
        },
    ]
    stat = _check_github_checks(checks)
    assert not stat


def test_check_github_checks_pending_plus_success_plus_fail():
    checks = [
        {
            'name': 'c1',
            'status': 'completed',
            'conclusion': 'error',
        },
        {
            'name': 'c2',
            'status': 'completed',
            'conclusion': 'failure',
        },
        {
            'name': 'c3',
            'status': 'blah',
            'conclusion': 'success',
        },
        {
            'name': 'c4',
            'status': 'completed',
            'conclusion': 'success',
        },
    ]
    stat = _check_github_checks(checks)
    assert not stat
