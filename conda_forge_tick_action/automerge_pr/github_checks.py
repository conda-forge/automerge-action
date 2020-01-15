import logging

from .defaults import IGNORED_CHECKS, BAD_STATES

LOGGER = logging.getLogger(__name__)


def check_github_checks(checks):
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
        return None, None
    else:
        if not all(v for v in check_states.values()):
            return False, "PR has failing or in progress checks"
        else:
            return True, None
