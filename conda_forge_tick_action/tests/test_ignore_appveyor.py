import os
import tempfile

import pytest

from ..automerge_pr import _ignore_appveyor


def test_ignore_appveyor_no_yaml():
    _environ = os.environ.copy()
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ['GITHUB_WORKSPACE'] = tmpdir
            os.makedirs(os.path.join(tmpdir, '.ci_support'), exist_ok=True)
            with open(os.path.join(tmpdir, '.ci_support', 'osx_.yaml'), 'w') as fp:
                fp.write("blah")
            with open(os.path.join(tmpdir, '.ci_support', 'linux_.yaml'), 'w') as fp:
                fp.write("blah")

            cfg = {}

            assert _ignore_appveyor(cfg)
    finally:
        os.environ.clear()
        os.environ.update(_environ)


@pytest.mark.parametrize('cfg', [
    {},
    {'provider': {}},
    {'provider': {'win': 'azure'}},
])
def test_ignore_appveyor_cfg(cfg):
    _environ = os.environ.copy()
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ['GITHUB_WORKSPACE'] = tmpdir
            os.makedirs(os.path.join(tmpdir, '.ci_support'), exist_ok=True)
            with open(os.path.join(tmpdir, '.ci_support', 'linux_.yaml'), 'w') as fp:
                fp.write("blah")

            assert _ignore_appveyor(cfg)
    finally:
        os.environ.clear()
        os.environ.update(_environ)


def test_ignore_appveyor_keep():
    _environ = os.environ.copy()
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ['GITHUB_WORKSPACE'] = tmpdir
            os.makedirs(os.path.join(tmpdir, '.ci_support'), exist_ok=True)
            with open(os.path.join(tmpdir, '.ci_support', 'win_.yaml'), 'w') as fp:
                fp.write("blah")
            with open(os.path.join(tmpdir, '.ci_support', 'linux_.yaml'), 'w') as fp:
                fp.write("blah")

            cfg = {'provider': {'win': 'appveyor'}}

            assert not _ignore_appveyor(cfg)
    finally:
        os.environ.clear()
        os.environ.update(_environ)
