# DEPRECATED & NO LONGER USED
**This docker image and automerge GHA are no longer used. Automerge now happens in the [conda-forge-webservices](https://github.com/conda-forge/conda-forge-webservices) repo.**

# automerge-action
[![tests](https://github.com/conda-forge/automerge-action/actions/workflows/tests.yml/badge.svg)](https://github.com/conda-forge/automerge-action/actions/workflows/tests.yml) [![pre-commit.ci status](https://results.pre-commit.ci/badge/github/conda-forge/automerge-action/main.svg)](https://results.pre-commit.ci/latest/github/conda-forge/automerge-action/main)

github action automerge on conda-forge

## Usage

To use this action, add the following YAML file at `.github/workflows/automerge.yml`

```yaml
on:
  status: {}
  check_suite:
    types:
      - completed
  workflow_run:
    workflows: ["Build conda package"]
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
        uses: conda-forge/automerge-action@main
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          rerendering_github_token: ${{ secrets.RERENDERING_GITHUB_TOKEN }}
```

## Opt-out or Opt-in

You can turn off PR automerging per feedstock by adding the following to the
`conda-forge.yml`

```yaml
bot:
  automerge: False
```

To ignore the linter, add the following.

```yaml
bot:
  automerge: False
  automerge_options:
    ignored_statuses:
      - linter
```

The default is currently `False` if these entries are not present. Set them to `True`
to turn on automerging.

## Deployment

The GitHub action always points to the `prod` tag of the
[condaforge/automerge-action](https://hub.docker.com/repository/docker/condaforge/automerge-action)
Docker image.

 - To redeploy the bot, push a new image to the `prod` tag.

   ```
   docker build -t condaforge/automerge-action:prod .
   docker push condaforge/automerge-action:prod
   ```

 - To take the bot down, delete the tag from the Docker repository. The GitHub Action
   will still run in this case, but it will always fail.

## Testing

The code has a test suite and will run live tests if the PR is from a repo branch.
However, you can test it live end-to-end with the bot by doing the following.

1. Bump the version of [this package](https://github.com/regro/cf-autotick-bot-test-package)
   by making a GitHub release. Then, after roughly an hour or so,
   [this feedstock](https://github.com/conda-forge/cf-autotick-bot-test-package-feedstock)
   should get an automerge PR with the version bump. Several other PRs are open on the feedstock and those
   should not be merged by the bot.

2. You can push an image to the `dev` tag of the Docker repo. Then, point the action in
   the `.github/workflows/automerge.yaml` of your testing repo to the `dev` branch of
   this repo by changing `conda-forge/automerge-action@main` to `conda-forge/automerge-action@dev`.

3. You can use the scripts in the `.scripts` directory to test the action live in a several cases.
   See the `README.md` in that directory for more information.
