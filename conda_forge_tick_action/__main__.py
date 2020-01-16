import os
import json
import logging

from .api_sessions import create_api_sessions
from .automerge import automerge_pr

LOGGER = logging.getLogger(__name__)


def main():
    logging.basicConfig(level=logging.INFO)

    LOGGER.info('making API clients')

    sess, gh = create_api_sessions(os.environ["INPUT_GITHUB_TOKEN"])

    with open(os.environ["GITHUB_EVENT_PATH"], 'r') as fp:
        event_data = json.load(fp)
    event_name = os.environ['GITHUB_EVENT_NAME'].lower()

    LOGGER.info('github event: %s', event_name)

    if event_name in ['status', 'check_run', 'schedule', 'push']:
        repo = gh.get_repo(os.environ['GITHUB_REPOSITORY'])
        for pr in repo.get_pulls():
            automerge_pr(repo, pr, sess)

    elif event_name in ['pull_request', 'pull_request_review']:
        event_data = event_data['pull_request']
        repo_name = event_data['base']['repo']['full_name']
        pr_num = int(event_data['number'])

        repo = gh.get_repo(repo_name)
        pr = repo.get_pull(pr_num)

        automerge_pr(repo, pr, sess)
    else:
        raise ValueError('GitHub event %s cannot be processed!' % event_name)
