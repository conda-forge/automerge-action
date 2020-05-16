import unittest.mock
from unittest.mock import MagicMock

import pytest

from ..automerge import automerge_pr


@unittest.mock.patch("conda_forge_tick_action.automerge._get_conda_forge_config")
def test_automerge_pr_bad_user(get_cfg_mock):
    get_cfg_mock.return_value = {}
    repo = MagicMock()
    repo.full_name = "go"

    pr = MagicMock()
    pr.user.login = 'blah'

    did_merge, reason = automerge_pr(repo, pr, None)

    assert not did_merge
    assert "user blah" in reason
    get_cfg_mock.assert_called_once_with(pr)


@unittest.mock.patch("conda_forge_tick_action.automerge._get_conda_forge_config")
def test_automerge_pr_no_title_slug(get_cfg_mock):
    get_cfg_mock.return_value = {}
    repo = MagicMock()
    repo.full_name = "go"

    pr = MagicMock()
    pr.user.login = 'regro-cf-autotick-bot'
    pr.title = "blah"

    did_merge, reason = automerge_pr(repo, pr, None)

    assert not did_merge
    assert "slug in the title" in reason
    get_cfg_mock.assert_called_once_with(pr)


@pytest.mark.parametrize('cfg', [
    {},
    {'bot': {}},
    {'bot': {'automerge': False}},
])
@unittest.mock.patch("conda_forge_tick_action.automerge._get_conda_forge_config")
def test_automerge_pr_feedstock_off(get_cfg_mock, cfg):
    get_cfg_mock.return_value = cfg
    repo = MagicMock()
    repo.full_name = "go"

    pr = MagicMock()
    pr.user.login = 'regro-cf-autotick-bot'
    pr.title = "[bot-automerge] blah"

    did_merge, reason = automerge_pr(repo, pr, None)

    assert not did_merge
    assert "off for this feedstock" in reason
    get_cfg_mock.assert_called_once_with(pr)


@pytest.mark.parametrize("fail", ["check", "status"])
@unittest.mock.patch("conda_forge_tick_action.automerge._get_conda_forge_config")
@unittest.mock.patch(
    'conda_forge_tick_action.automerge._get_required_checks_and_statuses')
@unittest.mock.patch('conda_forge_tick_action.automerge._get_github_checks')
@unittest.mock.patch('conda_forge_tick_action.automerge._get_github_statuses')
def test_automerge_pr_feedstock_status_or_check_fail(
    stat_mock, check_mock, req_mock, get_cfg_mock, fail
):
    check_mock.return_value = {"check1": True, "check2": True, "check3": False}
    stat_mock.return_value = {"status1": True, "status2": True, "status3": True}
    req_mock.return_value = ["check1", "check2", "status1", "status3"]
    get_cfg_mock.return_value = {'bot': {'automerge': True}}

    if fail == "check":
        check_mock.return_value["check2"] = False
    else:
        stat_mock.return_value["status1"] = False

    repo = MagicMock()
    repo.full_name = "go"

    pr = MagicMock()
    pr.user.login = 'regro-cf-autotick-bot'
    pr.title = "[bot-automerge] blah"

    did_merge, reason = automerge_pr(repo, pr, None)

    assert not did_merge
    assert "pending statuses" in reason
    get_cfg_mock.assert_called_once_with(pr)
    check_mock.assert_called_once_with(repo, pr, None)
    stat_mock.assert_called_once_with(repo, pr)
    req_mock.assert_called_once_with(pr, get_cfg_mock.return_value)


@unittest.mock.patch("conda_forge_tick_action.automerge._get_conda_forge_config")
@unittest.mock.patch(
    'conda_forge_tick_action.automerge._get_required_checks_and_statuses')
@unittest.mock.patch('conda_forge_tick_action.automerge._get_github_checks')
@unittest.mock.patch('conda_forge_tick_action.automerge._get_github_statuses')
def test_automerge_pr_feedstock_no_statuses_or_checks(
    stat_mock, check_mock, req_mock, get_cfg_mock
):
    check_mock.return_value = {}
    stat_mock.return_value = {}
    req_mock.return_value = []
    get_cfg_mock.return_value = {'bot': {'automerge': True}}

    repo = MagicMock()
    repo.full_name = "go"

    pr = MagicMock()
    pr.user.login = 'regro-cf-autotick-bot'
    pr.title = "[bot-automerge] blah"

    did_merge, reason = automerge_pr(repo, pr, None)

    assert not did_merge
    assert "At least one status or check must be required" in reason
    get_cfg_mock.assert_called_once_with(pr)
    check_mock.assert_called_once_with(repo, pr, None)
    stat_mock.assert_called_once_with(repo, pr)
    req_mock.assert_called_once_with(pr, get_cfg_mock.return_value)
