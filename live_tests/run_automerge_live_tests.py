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

import argparse
import contextlib
import os
import subprocess
import tempfile
import time
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
    _run_git_cmd("pull")

    data = (
        branch,
        "rerendering_github_token: ${{ secrets.RERENDERING_GITHUB_TOKEN }}",
    )

    with open(".github/workflows/automerge.yml", "w") as fp:
        fp.write(
            """\
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
"""
            % data
        )

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


print("making an edit to the head ref...")
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

                print("checkout branch...", flush=True)
                _run_git_cmd("checkout main")
                _run_git_cmd("checkout -b %s" % TEST_BRANCH)

                print("adding a correct recipe and conda-forge.yml...", flush=True)
                test_dir = os.path.dirname(__file__)
                subprocess.run(
                    f"cp {test_dir}/conda-forge.yml .",
                    shell=True,
                    check=True,
                )
                subprocess.run(
                    f"cp {test_dir}/meta.yaml recipe/meta.yaml",
                    shell=True,
                    check=True,
                )

                print("rerendering...", flush=True)
                subprocess.run(
                    "conda smithy rerender -c auto --no-check-uptodate",
                    shell=True,
                    check=True,
                )

                print("making a commit...", flush=True)
                _run_git_cmd("add .")
                _run_git_cmd("commit --allow-empty -m 'test commit for automerge'")

                print("push to branch...", flush=True)
                _run_git_cmd("push -u origin %s" % TEST_BRANCH)

                gh = github.Github(auth=github.Auth.Token(os.environ["GH_TOKEN"]))
                repo = gh.get_repo("conda-forge/cf-autotick-bot-test-package-feedstock")

                print("adding app token for workflow change permissions...", flush=True)
                repo.create_secret(
                    "RERENDERING_GITHUB_TOKEN",
                    os.environ["GH_TOKEN"],
                )

                print("making a PR...", flush=True)
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

                print("waiting for the PR to be merged...", flush=True)
                tot = 0
                merged = False
                while tot < 600:
                    time.sleep(10)
                    tot += 10
                    print("    slept %s seconds out of 600" % tot, flush=True)
                    if tot % 30 == 0 and pr.is_merged():
                        print("PR was merged!", flush=True)
                        merged = True
                        break

                if not merged:
                    raise RuntimeError("PR %d was not merged!" % pr.number)

            finally:
                _change_action_branch("main")

                print("closing PR if it is open...", flush=True)
                if pr is not None and not pr.is_merged():
                    pr.edit(state="closed")

                print("deleting the branch...", flush=True)
                _run_git_cmd("branch -d %s" % TEST_BRANCH)
                _run_git_cmd("push -d origin %s" % TEST_BRANCH)

                print("removing the secret...", flush=True)
                gh = github.Github(auth=github.Auth.Token(os.environ["GH_TOKEN"]))
                repo = gh.get_repo("conda-forge/cf-autotick-bot-test-package-feedstock")
                try:
                    repo.get_secret("RERENDERING_GITHUB_TOKEN").delete()
                except Exception:
                    pass
