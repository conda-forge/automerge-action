# regro-cf-autotick-bot-action
[![Build Status](https://travis-ci.com/regro/cf-autotick-bot-action.svg?branch=master)](https://travis-ci.com/regro/cf-autotick-bot-action)

github action for the conda-forge autotick bot

## Usage

To use this action, add the following YAML file at `.github/workflows/main.yml`

```yaml
on:
  status: {}
  check_run:
    types:
      - completed

jobs:
  regro-cf-autotick-bot-action:
    runs-on: ubuntu-latest
    name: regro-cf-autotick-bot-action
    steps:
      - name: checkout
        uses: actions/checkout@v2
      - name: regro-cf-autotick-bot-action
        id: regro-cf-autotick-bot-action
        uses: regro/cf-autotick-bot-action@master
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
```

## Deployment

The GitHub action always points to the `prod` tag of the
[condaforge/rego-cf-autotick-bot-action](https://hub.docker.com/repository/docker/condaforge/rego-cf-autotick-bot-action)
Docker image.

 - To redeploy the bot, push a new image to the `prod` tag.
 - To take the bot down, delete the tag from the Docker repository. The GitHub Action
   will still run in this case, but it will always fail.
