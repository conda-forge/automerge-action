import datetime

from ..automerge import _check_github_statuses


class DummyStatus(object):
    """Dummy object to mock up something from the API.

    We could use an actual mock, but shrug.
    """
    def __init__(self, context, state, updated_at):
        self.context = context
        self.state = state
        self.updated_at = updated_at


def test_check_github_statuses_ignores_linter():
    stat = _check_github_statuses([
        DummyStatus("conda-forge-linter", "success", datetime.datetime.now())
    ])
    assert stat is None


def test_check_github_statuses_extra_ignores():
    stat = _check_github_statuses(
        [
            DummyStatus("conda-forge-linter", "success", datetime.datetime.now()),
            DummyStatus("blah", "cess", datetime.datetime.now()),
        ],
        extra_ignored_statuses=["blah"],
    )
    assert stat is None


def test_check_github_statuses_nostatuses():
    stat = _check_github_statuses([])
    assert stat is None


def test_check_github_statuses_uses_latest():
    stat = _check_github_statuses(
        [
            DummyStatus("blah", "pending", datetime.datetime.now()),
            DummyStatus("blah", "success", datetime.datetime.now()),
        ],
    )
    assert stat


def test_heck_github_statuses_all_pending():
    stat = _check_github_statuses(
        [
            DummyStatus("blah", "pending", datetime.datetime.now()),
            DummyStatus("blah1", "pending", datetime.datetime.now()),
        ],
    )
    assert not stat


def test_heck_github_statuses_all_failure():
    stat = _check_github_statuses(
        [
            DummyStatus("blah", "failure", datetime.datetime.now()),
            DummyStatus("blah1", "error", datetime.datetime.now()),
        ],
    )
    assert not stat


def test_heck_github_statuses_all_success():
    stat = _check_github_statuses(
        [
            DummyStatus("blah", "success", datetime.datetime.now()),
            DummyStatus("blah1", "success", datetime.datetime.now()),
        ],
    )
    assert stat


def test_heck_github_statuses_pending_plus_failure():
    stat = _check_github_statuses(
        [
            DummyStatus("blah", "failure", datetime.datetime.now()),
            DummyStatus("blah1", "error", datetime.datetime.now()),
            DummyStatus("blah2", "pending", datetime.datetime.now()),
        ],
    )
    assert not stat


def test_heck_github_statuses_pending_plus_success():
    stat = _check_github_statuses(
        [
            DummyStatus("blah", "success", datetime.datetime.now()),
            DummyStatus("blah1", "error", datetime.datetime.now()),
            DummyStatus("blah2", "pending", datetime.datetime.now()),
        ],
    )
    assert not stat


def test_heck_github_statuses_success_plus_failure():
    stat = _check_github_statuses(
        [
            DummyStatus("blah", "success", datetime.datetime.now()),
            DummyStatus("blah1", "error", datetime.datetime.now()),
            DummyStatus("blah2", "failure", datetime.datetime.now()),
        ],
    )
    assert not stat


def test_heck_github_statuses_pending_plus_failure_plus_success():
    stat = _check_github_statuses(
        [
            DummyStatus("blah", "success", datetime.datetime.now()),
            DummyStatus("blah1", "error", datetime.datetime.now()),
            DummyStatus("blah2", "failure", datetime.datetime.now()),
            DummyStatus("blah3", "pending", datetime.datetime.now()),
        ],
    )
    assert not stat
