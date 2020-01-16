import os
import tempfile
import unittest.mock
from unittest.mock import MagicMock

import pytest
from ruamel.yaml import YAML
from ..automerge_pr import automerge_pr


def test_automerge_pr_bad_user():
    repo = MagicMock()
    repo.full_name = "go"

    pr = MagicMock()
    pr.user.login = 'blah'

    did_merge, reason = automerge_pr(repo, pr, None)

    assert not did_merge
    assert "user blah" in reason


def test_automerge_pr_no_title_slug():
    repo = MagicMock()
    repo.full_name = "go"

    pr = MagicMock()
    pr.user.login = 'regro-cf-autotick-bot'
    pr.title = "blah"

    did_merge, reason = automerge_pr(repo, pr, None)

    assert not did_merge
    assert "slug in the title" in reason


@pytest.mark.parametrize('cfg', [
    {},
    {'bot': {}},
    {'bot': {'automerge': False}},
])
def test_automerge_pr_feedstock_off(cfg):
    repo = MagicMock()
    repo.full_name = "go"

    pr = MagicMock()
    pr.user.login = 'regro-cf-autotick-bot'
    pr.title = "[bot-automerge] blah"

    _environ = os.environ.copy()
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ['GITHUB_WORKSPACE'] = tmpdir
            os.makedirs(os.path.join(tmpdir, '.ci_support'), exist_ok=True)
            with open(os.path.join(tmpdir, '.ci_support', 'osx_.yaml'), 'w') as fp:
                fp.write("blah")
            with open(os.path.join(tmpdir, '.ci_support', 'linux_.yaml'), 'w') as fp:
                fp.write("blah")

            yaml = YAML()
            with open(os.path.join(tmpdir, 'conda-forge.yml'), 'w') as fp:
                yaml.dump(cfg, fp)

            did_merge, reason = automerge_pr(repo, pr, None)

            assert not did_merge
            assert "off for this feedstock" in reason

    finally:
        os.environ.clear()
        os.environ.update(_environ)


@unittest.mock.patch('conda_forge_tick_action.automerge_pr._check_github_statuses')
def test_automerge_pr_feedstock_use_appveyor(_check_github_statuses_mk):
    _check_github_statuses_mk.return_value = False
    repo = MagicMock()
    repo.full_name = "go"

    pr = MagicMock()
    pr.user.login = 'regro-cf-autotick-bot'
    pr.title = "[bot-automerge] blah"

    _environ = os.environ.copy()
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ['GITHUB_WORKSPACE'] = tmpdir
            os.makedirs(os.path.join(tmpdir, '.ci_support'), exist_ok=True)
            with open(os.path.join(tmpdir, '.ci_support', 'win_.yaml'), 'w') as fp:
                fp.write("blah")
            with open(os.path.join(tmpdir, '.ci_support', 'linux_.yaml'), 'w') as fp:
                fp.write("blah")

            yaml = YAML()
            with open(os.path.join(tmpdir, 'conda-forge.yml'), 'w') as fp:
                yaml.dump(
                    {'bot': {'automerge': True}, 'provider': {'win': 'appveyor'}}, fp)

            did_merge, reason = automerge_pr(repo, pr, None)

            assert not did_merge
            assert "pending statuses" in reason
            assert (_check_github_statuses_mk.call_args[1]['extra_ignored_statuses']
                    is None)
    finally:
        os.environ.clear()
        os.environ.update(_environ)


@unittest.mock.patch('conda_forge_tick_action.automerge_pr._check_github_statuses')
def test_automerge_pr_feedstock_statuses_fail(_check_github_statuses_mk):
    _check_github_statuses_mk.return_value = False
    repo = MagicMock()
    repo.full_name = "go"

    pr = MagicMock()
    pr.user.login = 'regro-cf-autotick-bot'
    pr.title = "[bot-automerge] blah"

    _environ = os.environ.copy()
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ['GITHUB_WORKSPACE'] = tmpdir
            os.makedirs(os.path.join(tmpdir, '.ci_support'), exist_ok=True)
            with open(os.path.join(tmpdir, '.ci_support', 'osx_.yaml'), 'w') as fp:
                fp.write("blah")
            with open(os.path.join(tmpdir, '.ci_support', 'linux_.yaml'), 'w') as fp:
                fp.write("blah")

            yaml = YAML()
            with open(os.path.join(tmpdir, 'conda-forge.yml'), 'w') as fp:
                yaml.dump({'bot': {'automerge': True}}, fp)

            did_merge, reason = automerge_pr(repo, pr, None)

            assert not did_merge
            assert "pending statuses" in reason
            assert (_check_github_statuses_mk.call_args[1]['extra_ignored_statuses'] ==
                    ['continuous-integration/appveyor/pr'])

    finally:
        os.environ.clear()
        os.environ.update(_environ)


@unittest.mock.patch('conda_forge_tick_action.automerge_pr._get_checks')
@unittest.mock.patch('conda_forge_tick_action.automerge_pr._check_github_checks')
@unittest.mock.patch('conda_forge_tick_action.automerge_pr._check_github_statuses')
def test_automerge_pr_feedstock_checks_fail(
    _check_github_statuses_mk, _check_github_checks_mk, _get_checks_mk
):
    _check_github_statuses_mk.return_value = True
    _check_github_checks_mk.return_value = False
    repo = MagicMock()
    repo.full_name = "go"

    pr = MagicMock()
    pr.user.login = 'regro-cf-autotick-bot'
    pr.title = "[bot-automerge] blah"

    _environ = os.environ.copy()
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ['GITHUB_WORKSPACE'] = tmpdir
            os.makedirs(os.path.join(tmpdir, '.ci_support'), exist_ok=True)
            with open(os.path.join(tmpdir, '.ci_support', 'osx_.yaml'), 'w') as fp:
                fp.write("blah")
            with open(os.path.join(tmpdir, '.ci_support', 'linux_.yaml'), 'w') as fp:
                fp.write("blah")

            yaml = YAML()
            with open(os.path.join(tmpdir, 'conda-forge.yml'), 'w') as fp:
                yaml.dump({'bot': {'automerge': True}}, fp)

            did_merge, reason = automerge_pr(repo, pr, None)

            assert not did_merge
            assert "pending checks" in reason
            assert (_check_github_statuses_mk.call_args[1]['extra_ignored_statuses'] ==
                    ['continuous-integration/appveyor/pr'])

    finally:
        os.environ.clear()
        os.environ.update(_environ)


@unittest.mock.patch('conda_forge_tick_action.automerge_pr._get_checks')
@unittest.mock.patch('conda_forge_tick_action.automerge_pr._check_github_checks')
@unittest.mock.patch('conda_forge_tick_action.automerge_pr._check_github_statuses')
def test_automerge_pr_feedstock_no_statuses_or_checks(
    _check_github_statuses_mk, _check_github_checks_mk, _get_checks_mk
):
    _check_github_statuses_mk.return_value = None
    _check_github_checks_mk.return_value = None
    repo = MagicMock()
    repo.full_name = "go"

    pr = MagicMock()
    pr.user.login = 'regro-cf-autotick-bot'
    pr.title = "[bot-automerge] blah"

    _environ = os.environ.copy()
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ['GITHUB_WORKSPACE'] = tmpdir
            os.makedirs(os.path.join(tmpdir, '.ci_support'), exist_ok=True)
            with open(os.path.join(tmpdir, '.ci_support', 'osx_.yaml'), 'w') as fp:
                fp.write("blah")
            with open(os.path.join(tmpdir, '.ci_support', 'linux_.yaml'), 'w') as fp:
                fp.write("blah")

            yaml = YAML()
            with open(os.path.join(tmpdir, 'conda-forge.yml'), 'w') as fp:
                yaml.dump({'bot': {'automerge': True}}, fp)

            did_merge, reason = automerge_pr(repo, pr, None)

            assert not did_merge
            assert "No checks or statuses have returned success" in reason
            assert (_check_github_statuses_mk.call_args[1]['extra_ignored_statuses'] ==
                    ['continuous-integration/appveyor/pr'])

    finally:
        os.environ.clear()
        os.environ.update(_environ)
