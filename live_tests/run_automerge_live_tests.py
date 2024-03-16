"""
This script will run a live integration test of the automerge infrastructure.

1. Make sure you have a valid github token in your environment called
   "GH_TOKEN".
2. Make surre you have pushed the new version of the action to the `dev`
   docker image tag.

   You can run

      docker build -t condaforge/automerge-action:dev .
      docker push condaforge/automerge-action:dev

   or pass `--build-and-push` when running the test script.

Then you can execute this script and it will report the results.
"""
import os
import time
import tempfile
import contextlib
import subprocess
import argparse
import uuid
import github

TEST_BRANCH = "automerge-live-test-h%s" % uuid.uuid4().hex[:6]


@contextlib.contextmanager
def pushd(new_dir):
    previous_dir = os.getcwd()
    os.chdir(new_dir)
    try:
        yield
    finally:
        os.chdir(previous_dir)


def _run_git_cmd(cmd):
    subprocess.run("git %s" % cmd, shell=True, check=True)


def _change_action_branch(branch):
    print("moving repo to %s action" % branch, flush=True)
    _run_git_cmd("checkout main")

    data = (
        branch,
        "rerendering_github_token: ${{ secrets.RERENDERING_GITHUB_TOKEN }}",
    )

    with open(".github/workflows/automerge.yml", "w") as fp:
        fp.write("""\
on:
  status: {}
  check_suite:
    types:
      - completed

jobs:
  automerge-action:
    runs-on: ubuntu-latest
    name: automerge
    steps:
      - name: checkout
        uses: actions/checkout@v3
      - name: automerge-action
        id: automerge-action
        uses: conda-forge/automerge-action@%s
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          %s
""" % data)

    print("commiting...", flush=True)
    _run_git_cmd("add -f .github/workflows/automerge.yml")

    _run_git_cmd(
        "commit "
        "--allow-empty "
        "-m "
        "'[ci skip] move automerge action to branch %s'" % branch,
    )

    print("push to origin...", flush=True)
    _run_git_cmd("push")


parser = argparse.ArgumentParser(
    description="Run a live test of the automerge code",
)
parser.add_argument(
    "--build-and-push",
    help="build and push the docker image to the dev tag before running the tests",
    action="store_true",
)
args = parser.parse_args()

if args.build_and_push:
    subprocess.run(
        "docker build -t condaforge/automerge-action:dev .",
        shell=True,
        check=True,
    )
    subprocess.run(
        "docker push condaforge/automerge-action:dev",
        shell=True,
        check=True,
    )


print('making an edit to the head ref...')
with tempfile.TemporaryDirectory() as tmpdir:
    with pushd(tmpdir):
        print("cloning...")
        _run_git_cmd(
            "clone "
            "https://x-access-token:${GH_TOKEN}@github.com/conda-forge/"
            "cf-autotick-bot-test-package-feedstock.git",
        )

        with pushd("cf-autotick-bot-test-package-feedstock"):
            pr = None
            try:
                _change_action_branch("dev")

                print("checkout branch...")
                _run_git_cmd("checkout main")
                _run_git_cmd(
                    "checkout -b %s" % TEST_BRANCH
                )

                print("making a commit...")
                _run_git_cmd("commit --allow-empty -m 'test commit for automerge'")

                print("push to branch...")
                _run_git_cmd("push -u origin %s" % TEST_BRANCH)

                print("making a PR...")
                gh = github.Github(auth=github.Auth.Token(os.environ["GH_TOKEN"]))
                repo = gh.get_repo("conda-forge/cf-autotick-bot-test-package-feedstock")
                pr = repo.create_pull(
                    "main",
                    TEST_BRANCH,
                    title="[DO NOT TOUCH] test pr for automerge",
                    body=(
                        "This is a test PR for automerge from GHA run %s. "
                        "Please do not touch." % os.environ["GHA_URL"]
                    ),
                    maintainer_can_modify=True,
                    draft=False,
                )
                pr.add_to_labels("automerge")

                print("waiting for the PR to be merged...")
                tot = 0
                while tot < 300:
                    time.sleep(10)
                    tot += 10
                    print("    slept %s seconds out of 300" % tot, flush=True)

                if not pr.is_merged():
                    raise RuntimeError("PR %d was not merged!" % pr.number)

            finally:
                _change_action_branch("main")

                if pr is not None and not pr.is_merged():
                    pr.edit(state="closed")
