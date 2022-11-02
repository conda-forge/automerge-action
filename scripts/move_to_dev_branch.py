#!/user/bin/env python
import subprocess


with open("../cf-test-master/.github/workflows/automerge.yml", "w") as fp:
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
        uses: actions/checkout@v2
      - name: automerge-action
        id: automerge-action
        uses: conda-forge/automerge-action@dev
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          rerendering_github_token: ${{ secrets.RERENDERING_GITHUB_TOKEN }}
""")

subprocess.run(
    "cd ../cf-test-master && "
    "git checkout main && "
    "git pull && "
    "git add .github/workflows/automerge.yml && "
    "git ci --allow-empty -m '[ci skip] automerge to dev' && "
    "git push",
    shell=True,
    check=True,
)
