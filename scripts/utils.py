import subprocess


def move_action_to_dev():
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
        uses: conda-forge/automerge-action@dev
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          rerendering_github_token: ${{ secrets.RERENDERING_GITHUB_TOKEN }}
"""
        )

    subprocess.run(
        "git add .github/workflows/automerge.yml && "
        "git commit --allow-empty -m 'automerge to dev' && "
        "git push",
        shell=True,
        check=True,
    )
