import os
import json
import logging
import pprint

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

    raise_error = False
    if event_name in ['status', 'check_suite']:
        if event_name == 'status':
            sha = event_data['sha']
        elif event_name == 'check_suite':
            sha = event_data['check_suite']['head_sha']

        repo = gh.get_repo(os.environ['GITHUB_REPOSITORY'])
        for pr in repo.get_pulls():
            if pr.head.sha == sha:
                automerge_pr(repo, pr, sess)

    elif event_name in ['pull_request', 'pull_request_review']:
        event_data = event_data['pull_request']
        repo_name = event_data['base']['repo']['full_name']
        pr_num = int(event_data['number'])

        repo = gh.get_repo(repo_name)
        pr = repo.get_pull(pr_num)

        automerge_pr(repo, pr, sess)
    else:
        raise_error = True

    print(
        "\n\n===================================================================="
        "===============================",
        flush=True,
    )
    print(
        "=================================================================="
        "=================================",
        flush=True,
    )
    LOGGER.info('github event data:\n%s\n\n', pprint.pformat(event_data))

    if raise_error:
        raise ValueError('GitHub event %s cannot be processed!' % event_name)
