# automerge-action

a docker image to run conda-forge's bot automerge GitHub Actions integration

## Description

This image contains the code and integrations to run conda-forge's bot automerge GitHub Actions
integrations. This image is used by the autotick bot to automatically merge passing PRs if the feedstock
maintainers have opted in.

## License

This image is licensed under [BSD-3 Clause](https://github.com/conda-forge/automerge-action/blob/main/LICENSE)
and is based on a base image under the [MIT](https://github.com/conda-forge/automerge-action/blob/main/BASE_IMAGE_LICENSE)
license.

## Documentation & Contributing

You can find documentation for how to use the image on the
upstream [repo](https://github.com/conda-forge/automerge-action) and in the sections below.

To get in touch with the maintainers of this image, please [make an issue](https://github.com/conda-forge/automerge-action/issues/new/choose)
and bump the `@conda-forge/core` team.

Contributions are welcome in accordance
with conda-forge's [code of conduct](https://conda-forge.org/community/code-of-conduct/). We accept them through pull requests on the
upstream [repo](https://github.com/conda-forge/automerge-action/compare).

## Important Image Tags

 - prod: the current production image in use for feedstocks
 - dev: a tag that is overwritten and used for CI testing

## Getting Started & Usage

To use this action, add the following YAML file at `.github/workflows/automerge.yml`

```yaml
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
        uses: conda-forge/automerge-action@main
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          rerendering_github_token: ${{ secrets.RERENDERING_GITHUB_TOKEN }}
```
