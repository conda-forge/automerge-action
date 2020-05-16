import requests
import urllib3.util.retry

from github import Github


def create_api_sessions(github_token):
    """Create API sessions for GitHub.

    Parameters
    ----------
    github_token : str
        The GitHub access token.

    Returns
    -------
    session : requests.Session
        A `requests` session w/ the beta `check_run` API configured.
    gh : github.MainClass.Github
        A `Github` object from the PyGithub package.
    """
    # based on
    #  https://alexwlchan.net/2019/03/
    #    creating-a-github-action-to-auto-merge-pull-requests/
    # with lots of edits
    sess = requests.Session()
    sess.headers = {
        "Accept": "; ".join([
            "application/vnd.github.v3+json",
            # special beta api for check_suites endpoint
            "application/vnd.github.antiope-preview+json",
        ]),
        "Authorization": f"token {github_token}",
        "User-Agent": f"GitHub Actions script in {__file__}"
    }

    def raise_for_status(resp, *args, **kwargs):
        try:
            resp.raise_for_status()
        except Exception as e:
            print('ERROR:', resp.text)
            raise e

    sess.hooks["response"].append(raise_for_status)

    # build a github object too
    gh = Github(
        github_token,
        retry=urllib3.util.retry.Retry(total=10, backoff_factor=0.1))

    return sess, gh
