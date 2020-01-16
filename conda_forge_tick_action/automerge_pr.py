import os
import glob
import logging
import datetime

LOGGER = logging.getLogger(__name__)

# action always ignores itself
# github actions use the check_run API
IGNORED_CHECKS = ['regro-cf-autotick-bot-action']


# always ignore the linter since it is not reliable
IGNORED_STATUSES = ['conda-forge-linter']

# sets of states that indicate good / bad / neutral in the github API
NEUTRAL_STATES = ['pending']
BAD_STATES = ['failure', 'error']


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
        if check['name'] not in IGNORED_CHECKS:
            if check['status'] != 'completed':
                check_states[check['name']] = None
            else:
                if check['conclusion'] in BAD_STATES:
                    check_states[check['name']] = False
                else:
                    check_states[check['name']] = True

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
    """Should we ignore appveyor?

    Parameters
    ----------
    cfg : dict
        The `conda-forge.yml` as a dictionary.

    Returns
    -------
    stat : bool
        If `True`, ignore appveyor, otherwise do not.
    """
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
