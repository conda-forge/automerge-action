import os
import logging
import datetime
import subprocess
import tempfile
import contextlib
import time
import random

from ruamel.yaml import YAML
import tenacity

LOGGER = logging.getLogger(__name__)

ALLOWED_USERS = ['regro-cf-autotick-bot']

# action always ignores itself
# github actions use the check_suite API
IGNORED_CHECKS = ['github-actions']

# sets of states that indicate good / bad / neutral in the github API
NEUTRAL_STATES = ['pending']
BAD_STATES = [
    # for statuses
    'failure', 'error',
    # for checks
    'action_required', 'canceled', 'timed_out', 'failed', 'neutral']
GOOD_MERGE_STATES = ["clean", "has_hooks", "unknown", "unstable"]


# https://stackoverflow.com/questions/6194499/pushd-through-os-system
@contextlib.contextmanager
def pushd(new_dir):
    previous_dir = os.getcwd()
    os.chdir(new_dir)
    try:
        yield
    finally:
        os.chdir(previous_dir)


def _run_git_command(*args):
    try:
        c = subprocess.run(
            ["git"] + list(args),
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
    except subprocess.CalledProcessError as e:
        print(c.stdout)
        raise e


def _get_conda_forge_config(pr):
    """get the conda-forge.yml from upstream master

    We always do this to make sure we use the maintainer settings and not
    any from a fork.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        _run_git_command("clone", pr.base.repo.clone_url, tmpdir)
        with pushd(tmpdir):
            _run_git_command("checkout", pr.base.ref)
            with open("conda-forge.yml", "r") as fp:
                cfg = YAML().load(fp)
    return cfg


def _automerge_me(cfg):
    """Compute if feedstock allows automerges from `conda-forge.yml`"""
    # TODO turn False to True when we default to automerge
    return cfg.get('bot', {}).get('automerge', False)


@tenacity.retry(
    stop=tenacity.stop_after_attempt(10),
    wait=tenacity.wait_random_exponential(multiplier=0.1))
def _get_checks(repo, pr, session):
    return (
        session
        .get(
            "https://api.github.com/repos/%s/commits/%s/check-suites" % (
                repo.full_name, pr.head.sha)
        )
        .json()['check_suites']
    )


def _get_github_checks(repo, pr, session):
    """Get all of the github checks associated with a PR.

    Parameters
    ----------
    repo : github.Repository.Repository
        A `Repository` object for the given repo from the PyGithub package.
    pr : github.PullRequest.PullRequest
        A `PullRequest` object for the given PR from the PuGithhub package.
    session : requests.Session
        A `requests` session w/ the correct headers for the GitHub API v3.
        See `conda_forge_tick_action.api_sessions.create_api_sessions` for
        details.

    Returns
    -------
    check_states : dict of bool or None
        A dictionary mapping each check to its state.
    """

    checks = _get_checks(repo, pr, session)

    check_states = {}
    for check in checks:
        name = check['app']['slug']
        if name not in IGNORED_CHECKS:
            if check['status'] != 'completed':
                check_states[name] = None
            else:
                if check['conclusion'] == "success":
                    check_states[name] = True
                else:
                    check_states[name] = False

    for name, good in check_states.items():
        LOGGER.info('check: name|state = %s|%s', name, good)

    return check_states


def _get_github_statuses(repo, pr):
    """Get all of the github statuses associated with a PR.

    Parameters
    ----------
    repo : github.Repository.Repository
        A `Repository` object for the given repo from the PyGithub package.
    pr : github.PullRequest.PullRequest
        A `PullRequest` object for the given PR from the PuGithhub package.

    Returns
    -------
    status_states : dict of bool or None
        A dictionary mapping each status to its state.
    """
    # github emits all of the statuses with a time stamp as events
    # you have to keep the latest one
    # so this is why we compare the times below

    commit = repo.get_commit(pr.head.sha)
    statuses = commit.get_statuses()

    status_states = {}
    for status in statuses:
        if status.context not in status_states:
            # init with really old time
            status_states[status.context] = (
                None,
                datetime.datetime.now() - datetime.timedelta(weeks=10000))

        if status.state in NEUTRAL_STATES:
            if status.updated_at > status_states[status.context][1]:
                status_states[status.context] = (
                    None,
                    status.updated_at)
        elif status.state in BAD_STATES:
            if status.updated_at > status_states[status.context][1]:
                status_states[status.context] = (
                    False,
                    status.updated_at)
        else:
            if status.updated_at > status_states[status.context][1]:
                status_states[status.context] = (
                    True,
                    status.updated_at)

    for context, val in status_states.items():
        LOGGER.info('status: name|state = %s|%s', context, val[0])

    return {k: v[0] for k, v in status_states.items()}


def _circle_is_active():
    """check if circle is active"""
    if os.path.exists(".circleci/checkout_merge_commit.sh"):
        return True

    if os.path.exists(".circleci/fast_finish_ci_pr_build.sh"):
        return True

    # we now look for this sentinel text
    #      filters:
    #        branches:
    #          ignore:
    #            - /.*/
    with open(".circleci/config.yml", "r") as fp:
        start = False
        ind = 0
        sentinels = ["filters:", "branches:", "ignore:", "- /.*/"]
        found_sentinels = [False] * len(sentinels)
        for line in fp.readlines():
            if line.strip() == "filters:":
                start = True
            if start and ind < len(sentinels):
                if line.strip() == sentinels[ind]:
                    found_sentinels[ind] = True
                ind += 1

    if all(found_sentinels):
        return False
    else:
        return True


def _get_required_checks_and_statuses(pr, cfg):
    """return a list of required statuses and checks"""
    ignored_statuses = cfg.get(
        'bot', {}).get(
            'automerge_options', {}).get(
                'ignored_statuses', [])
    required = ["linter"]

    with tempfile.TemporaryDirectory() as tmpdir:
        _run_git_command("clone", pr.head.repo.clone_url, tmpdir)
        with pushd(tmpdir):
            _run_git_command("checkout", pr.head.sha)

            if os.path.exists("appveyor.yml") or os.path.exists(".appveyor.yml"):
                required.append("appveyor")

            if os.path.exists(".drone.yml"):
                required.append("drone")

            if os.path.exists(".travis.yml"):
                required.append("travis")

            if os.path.exists("azure-pipelines.yml"):
                required.append("azure")

            # smithy writes this config even if circle is off, but we can check
            # for other things
            if (
                os.path.exists(".circleci/config.yml")
                and _circle_is_active()
            ):
                required.append("circle")

    return [
        r.lower()
        for r in required
        if not any(r.lower() in _i for _i in ignored_statuses)
    ]


def _all_statuses_and_checks_ok(
    status_states, check_states, req_checks_and_states
):
    """check all of the required statuses are OK and return their states"""
    final_states = {r: None for r in req_checks_and_states}
    for req in req_checks_and_states:
        found_state = False
        for k, s in status_states.items():
            if req in k.lower():
                if not found_state:
                    found_state = True
                    state = s
                else:
                    state = state and s

        for k, s in check_states.items():
            if req in k.lower():
                if not found_state:
                    found_state = True
                    state = s
                else:
                    state = state and s

        final_states[req] = None if not found_state else state
        LOGGER.info('final status: name|state = %s|%s', req, final_states[req])

    return all(v for v in final_states.values()), final_states


def _check_pr(pr, cfg):
    """make sure a PR is ok to automerge"""
    if any(label.name == "automerge" for label in pr.get_labels()):
        return True, None

    # only allowed users
    if pr.user.login not in ALLOWED_USERS:
        return False, "user %s cannot automerge" % pr.user.login

    # only if [bot-automerge] is in the pr title
    if '[bot-automerge]' not in pr.title:
        return False, "PR does not have the '[bot-automerge]' slug in the title"

    # can we automerge in this feedstock?
    if not _automerge_me(cfg):
        return False, "automated bot merges are turned off for this feedstock"

    return True, None


def _comment_on_pr(pr, stats, msg, check_race=1):
    # do not comment if pending
    if any(v is None for v in stats.values()):
        return

    comment = """\
Hi! This is the friendly conda-forge automerge bot!

I considered the following status checks when analyzing this PR:
"""
    for k, v in stats.items():
        if v:
            _v = "passed"
        elif v is None:
            _v = "pending"
        else:
            _v = "failed"
        comment = comment + " - **%s**: %s\n" % (k, _v)

    comment = comment + "\n\nThus the PR was %s" % msg

    # the times at which PR statuses return are correlated and so this code
    # can race when posting failures
    # thus we can turn up check_race to say 10
    # in that case to try and randomize to avoid double posting comments
    # I considered using app slugs (e.g. require the failed check to be triggered
    # by the same app as a failed one in the final statuses). However, some apps
    # post more than one message (e.g., circle) so that would not work if they both
    # fail.
    # I also thought about using timestamps, but github check events don't come
    # with one.
    last_comment = None
    i = 0
    while last_comment is None and i < check_race:
        for cmnt in pr.get_issue_comments():
            if "Hi! This is the friendly conda-forge automerge bot!" in cmnt.body:
                last_comment = cmnt
        time.sleep(random.uniform(0.5, 1.5))
        i += 1

    if last_comment is None:
        pr.create_issue_comment(comment)
    else:
        last_comment.edit(comment)


def _automerge_pr(repo, pr, session):
    cfg = _get_conda_forge_config(pr)
    allowed, msg = _check_pr(pr, cfg)

    if not allowed:
        return False, msg

    # get checks and statuses
    status_states = _get_github_statuses(repo, pr)
    check_states = _get_github_checks(repo, pr, session)

    # get which ones are required
    req_checks_and_states = _get_required_checks_and_statuses(pr, cfg)
    if len(req_checks_and_states) == 0:
        return False, "At least one status or check must be required"

    ok, final_statuses = _all_statuses_and_checks_ok(
        status_states, check_states, req_checks_and_states
    )
    if not ok:
        _comment_on_pr(pr, final_statuses, "not passing and not merged.", check_race=2)
        return False, "PR has failing or pending statuses/checks"

    # make sure PR is mergeable and not already merged
    if pr.is_merged():
        return False, "PR has already been merged"
    if (
        pr.mergeable is None or
        not pr.mergeable or
        pr.mergeable_state not in GOOD_MERGE_STATES
    ):
        _comment_on_pr(
            pr,
            final_statuses,
            "passing, but not in a mergeable state (mergeable=%s, "
            "mergeable_state=%s)." % (
                pr.mergeable, pr.mergeable_state
            ),
            check_race=2,
        )
        return False, "PR merge issue: mergeable|mergeable_state = %s|%s" % (
            pr.mergeable, pr.mergeable_state)

    # we're good - now merge
    merge_status = pr.merge(
        commit_message="automerged PR by regro-cf-autotick-bot-action",
        commit_title=pr.title,
        merge_method='merge',
        sha=pr.head.sha)
    if not merge_status.merged:
        _comment_on_pr(
            pr,
            final_statuses,
            "passing, but could not be merged (error=%s)." % merge_status.message,
            check_race=2,
        )
        return (
            False,
            "PR could not be merged: message %s" % merge_status.message)
    else:
        # use a smaller check_race here to make sure this one is prompt
        _comment_on_pr(
            pr, final_statuses, "passing and merged! Have a great day!", check_race=2)
        return True, "all is well :)"


def automerge_pr(repo, pr, session):
    """Possibly automerge a PR.

    Parameters
    ----------
    repo : github.Repository.Repository
        A `Repository` object for the given repo from the PyGithub package.
    pr : github.PullRequest.PullRequest
        A `PullRequest` object for the given PR from the PuGithhub package.
    session : requests.Session
        A `requests` session w/ the correct headers for the GitHub API v3.
        See `conda_forge_tick_action.api_sessions.create_api_sessions` for
        details.

    Returns
    -------
    did_merge : bool
        If `True`, the merge was done, `False` if not.
    reason : str
        The reason the merge worked or did not work.
    """
    did_merge, reason = _automerge_pr(repo, pr, session)

    if did_merge:
        LOGGER.info(
            'MERGED PR %s on %s: %s',
            pr.number, repo.full_name, reason)
    else:
        LOGGER.info(
            'DID NOT MERGE PR %s on %s: %s',
            pr.number, repo.full_name, reason)

    return did_merge, reason
