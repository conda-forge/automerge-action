import os
import glob
import logging
import datetime

from ruamel.yaml import YAML
import tenacity

LOGGER = logging.getLogger(__name__)

ALLOWED_USERS = ['regro-cf-autotick-bot']

# action always ignores itself
# github actions use the check_suite API
IGNORED_CHECKS = ['github-actions']

# always ignore the linter since it is not reliable
IGNORED_STATUSES = ['conda-forge-linter']

# sets of states that indicate good / bad / neutral in the github API
NEUTRAL_STATES = ['pending']
BAD_STATES = ['failure', 'error']
GOOD_MERGE_STATES = ["clean", "has_hooks", "unknown", "unstable"]


def _automerge_me(cfg):
    """Compute if feedstock allows automeges from `conda-forge.yml`"""
    # TODO turn False to True when we default to automerge
    return cfg.get('bot', {}).get('automerge', False)


@tenacity.retry(
    stop=tenacity.stop_after_attempt(10),
    wait=tenacity.wait_random_exponential(multiplier=0.1))
def _get_checks(repo, pr, session):
    return session.get(
        "https://api.github.com/repos/%s/commits/%s/check-suites" % (
            repo.full_name, pr.head.sha))


def _check_github_checks(checks):
    """Check if all of the checks are ok.

    Parameters
    ----------
    checks : list of dicts
        A list of the check json blobs as dicts.

    Returns
    -------
    state : bool or None
        The state. `True` if all have passed, `False` if there are
        any failures or pending checks, `None` if there are no input checks.
    """
    check_states = {}
    for check in checks:
        name = check['app']['slug']
        if name not in IGNORED_CHECKS:
            if check['status'] != 'completed':
                check_states[name] = None
            else:
                if check['conclusion'] in BAD_STATES:
                    check_states[name] = False
                else:
                    check_states[name] = True

    for name, good in check_states.items():
        LOGGER.info('check: name|state = %s|%s', name, good)

    if len(check_states) == 0:
        return None
    else:
        if not all(v for v in check_states.values()):
            return False
        else:
            return True


def _check_github_statuses(statuses, extra_ignored_statuses=None):
    """Check that the statuses are ok.

    Note this function always ignores contexts in `IGNORED_STATUSES`
    which typically includes 'conda-forge-linter'.

    Parameters
    ----------
    statuses : iterable of `github.CommitStatus.CommitStatus`
        An iterable of statuses.
    extra_ignored_statuses : list of str
        A list of status context values to also ignore.

    Returns
    -------
    state : bool or None
        The state. `True` if all have passed, `False` if there are
        any failures or pending checks, `None` if there are no input checks.
    """
    # github emits all of the statuses with a time stamp as events
    # you have to keep the latest one
    # so this is why we compare the times below

    extra_ignored_statuses = extra_ignored_statuses or []

    status_states = {}
    for status in statuses:
        if status.context in IGNORED_STATUSES + extra_ignored_statuses:
            continue

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

    if len(status_states) == 0:
        return None
    else:
        if not all(val[0] for val in status_states.values()):
            return False
        else:
            return True


def _ignore_appveyor(cfg):
    """Compute if we should ignore appveyor from the `conda-forge.yml`."""
    fnames = glob.glob(
        os.path.join(os.environ['GITHUB_WORKSPACE'], '.ci_support', 'win*.yaml')
    )

    # windows is not on, so skip
    if len(fnames) == 0:
        return True

    # windows is on but maybe we only care about azure?
    if cfg.get('provider', {}).get('win', 'azure') in ['azure', 'default']:
        return True

    return False


def _check_pr(pr, cfg):
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


def _automerge_pr(repo, pr, session):
    # load the the conda-forge config
    with open(os.path.join(os.environ['GITHUB_WORKSPACE'], 'conda-forge.yml')) as fp:
        cfg = YAML().load(fp)

    allowed, msg = _check_pr(pr, cfg)

    if not allowed:
        return False, msg

    # now check statuses
    commit = repo.get_commit(pr.head.sha)
    statuses = commit.get_statuses()
    if _ignore_appveyor(cfg):
        extra_ignored_statuses = ['continuous-integration/appveyor/pr']
    else:
        extra_ignored_statuses = None
    status_ok = _check_github_statuses(
        statuses,
        extra_ignored_statuses=extra_ignored_statuses,
    )
    if not status_ok and status_ok is not None:
        return False, "PR has failing or pending statuses"

    # now check checks
    checks = _get_checks(repo, pr, session)
    checks_ok = _check_github_checks(checks.json()['check_suites'])
    if not checks_ok and checks_ok is not None:
        return False, "PR has failing or pending checks"

    # we need to have at least one check
    if checks_ok is None and status_ok is None:
        return False, "No checks or statuses have returned success"

    # make sure PR is mergeable and not already merged
    if pr.is_merged():
        return False, "PR has already been merged"
    if (pr.mergeable is None or
            not pr.mergeable or
            pr.mergeable_state not in GOOD_MERGE_STATES):
        return False, "PR merge issue: mergeable|mergeable_state = %s|%s" % (
            pr.mergeable, pr.mergeable_state)

    # we're good - now merge
    merge_status = pr.merge(
        commit_message="automerged PR by regro-cf-autotick-bot-action",
        commit_title=pr.title,
        merge_method='squash',
        sha=pr.head.sha)
    if not merge_status.merged:
        return (
            False,
            "PR could not be merged: message %s" % merge_status.message)
    else:
        return True, "all is well :)"


def automerge_pr(repo, pr, session):
    """Possibly automege a PR.

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
