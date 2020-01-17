from ..automerge import _check_github_checks


def test_check_github_checks_nochecks():
    stat = _check_github_checks([])
    assert stat is None


def test_check_github_checks_ignores_self():
    checks = [
        {
            'app': {'slug': 'github-actions'},
            'status': 'blah',
            'conclusion': 'blah',
        },
    ]
    stat = _check_github_checks(checks)
    assert stat is None


def test_check_github_checks_all_pending():
    checks = [
        {
            'app': {'slug': 'c1'},
            'status': 'blah',
            'conclusion': 'blah',
        },
        {
            'app': {'slug': 'c2'},
            'status': 'blah',
            'conclusion': 'blah',
        },
    ]
    stat = _check_github_checks(checks)
    assert not stat


def test_check_github_checks_all_fail():
    checks = [
        {
            'app': {'slug': 'c1'},
            'status': 'completed',
            'conclusion': 'error',
        },
        {
            'app': {'slug': 'c2'},
            'status': 'completed',
            'conclusion': 'failure',
        },
    ]
    stat = _check_github_checks(checks)
    assert not stat


def test_check_github_checks_all_success():
    checks = [
        {
            'app': {'slug': 'c1'},
            'status': 'completed',
            'conclusion': 'success',
        },
        {
            'app': {'slug': 'c2'},
            'status': 'completed',
            'conclusion': 'success',
        },
    ]
    stat = _check_github_checks(checks)
    assert stat


def test_check_github_checks_success_plus_pending():
    checks = [
        {
            'app': {'slug': 'c1'},
            'status': 'blah',
            'conclusion': 'success',
        },
        {
            'app': {'slug': 'c2'},
            'status': 'completed',
            'conclusion': 'success',
        },
    ]
    stat = _check_github_checks(checks)
    assert not stat


def test_check_github_checks_success_plus_fail():
    checks = [
        {
            'app': {'slug': 'c1'},
            'status': 'completed',
            'conclusion': 'error',
        },
        {
            'app': {'slug': 'c2'},
            'status': 'completed',
            'conclusion': 'failure',
        },
        {
            'app': {'slug': 'c3'},
            'status': 'completed',
            'conclusion': 'success',
        },
    ]
    stat = _check_github_checks(checks)
    assert not stat


def test_check_github_checks_pending_plus_fail():
    checks = [
        {
            'app': {'slug': 'c1'},
            'status': 'completed',
            'conclusion': 'error',
        },
        {
            'app': {'slug': 'c2'},
            'status': 'completed',
            'conclusion': 'failure',
        },
        {
            'app': {'slug': 'c3'},
            'status': 'blah',
            'conclusion': 'success',
        },
    ]
    stat = _check_github_checks(checks)
    assert not stat


def test_check_github_checks_pending_plus_success_plus_fail():
    checks = [
        {
            'app': {'slug': 'c1'},
            'status': 'completed',
            'conclusion': 'error',
        },
        {
            'app': {'slug': 'c2'},
            'status': 'completed',
            'conclusion': 'failure',
        },
        {
            'app': {'slug': 'c3'},
            'status': 'blah',
            'conclusion': 'success',
        },
        {
            'app': {'slug': 'c4'},
            'status': 'completed',
            'conclusion': 'success',
        },
    ]
    stat = _check_github_checks(checks)
    assert not stat
