#!/user/bin/env python
import os
import sys
import github
import subprocess
import yaml
import uuid


META = """\
{% set name = "cf-autotick-bot-test-package" %}
{% set version = "0.9" %}

package:
  name: {{ name|lower }}
  version: {{ version }}

source:
  url: https://github.com/regro/cf-autotick-bot-test-package/archive/v{{ version }}.tar.gz
  sha256: 74d5197d4ca8afb34b72a36fc8763cfaeb06bdbc3f6d63e55099fe5e64326048

build:
  number: {{ build }}
  string: "{{ cislug }}_py{{ py }}h{{ PKG_HASH }}_{{ build }}"
  skip: True  # [py != 38]

requirements:
  host:
    - python
    - pip
  run:
    - python

test:
  commands:
    - echo "works!"

about:
  home: https://github.com/regro/cf-scripts
  license: BSD-3-Clause
  license_family: BSD
  license_file: LICENSE
  summary: testing feedstock for the regro-cf-autotick-bot

extra:
  recipe-maintainers:
    - beckermr
    - conda-forge/bot
"""  # noqa

assert sys.argv[3][0] == "v"
assert isinstance(int(sys.argv[3][1:]), int)

BUILD_SLUG = "{% set build = " + str(int(sys.argv[3][1:]) + 14) + " %}\n"

CI_SLUG = '{% set cislug = "' + sys.argv[1] + sys.argv[2] + '" %}\n'

TST = sys.argv[3]

uid = "h" + uuid.uuid4().hex[0:6]
BASE_BRANCH = "%s-%s-%s-commit-after" % (uid, sys.argv[1], sys.argv[2])
BRANCH = TST + "-" + BASE_BRANCH

print("\n\n=========================================")
print("making the base branch")
try:
    subprocess.run(
        "pushd ../cf-test-master && "
        "git checkout master && "
        "git reset --hard HEAD && "
        "git checkout -b %s && "
        "git push --set-upstream origin %s && "
        "popd" % (BASE_BRANCH, BASE_BRANCH),
        shell=True,
        check=True,
    )
except Exception:
    subprocess.run(
        "pushd ../cf-test-master && "
        "git checkout %s && "
        "git push --set-upstream origin %s && "
        "popd" % (BASE_BRANCH, BASE_BRANCH),
        shell=True,
    )

print("\n\n=========================================")
print("making the head branch")
subprocess.run(
    ["git", "reset", "--hard", "HEAD"],
    check=True,
)

subprocess.run(
    ["git", "pull", "upstream", BASE_BRANCH],
    check=True,
)

subprocess.run(
    ["git", "checkout", BASE_BRANCH],
    check=True,
)

subprocess.run(
    ["git", "pull", "upstream", BASE_BRANCH],
    check=True,
)

subprocess.run(
    ["git", "checkout", "-b", BRANCH],
    check=True,
)

print("\n\n=========================================")
print("editing the recipe")

with open("recipe/meta.yaml", "w") as fp:
    fp.write(CI_SLUG)
    fp.write(BUILD_SLUG)
    fp.write(META)

with open("conda-forge.yml", "r") as fp:
    cfg = yaml.safe_load(fp)

cfg["provider"]["linux"] = sys.argv[1]
cfg["provider"]["osx"] = sys.argv[2]
prov = cfg["provider"]
if "linux_ppc64le" in prov:
    del prov["linux_ppc64le"]
if "linux_aarch64" in prov:
    del prov["linux_aarch64"]

with open("conda-forge.yml", "w") as fp:
    yaml.dump(cfg, fp)

subprocess.run(
    ["git", "add", "conda-forge.yml", "recipe/meta.yaml"],
    check=True,
)

print("\n\n=========================================")
print("rerendering")

subprocess.run(
    ["conda", "smithy", "rerender", "-c", "auto"],
    check=True
)

print("\n\n=========================================")
print("pushing to the fork")

subprocess.run(
    ["git", "push", "--set-upstream", "origin", BRANCH],
    check=True,
)

print("\n\n=========================================")
print("making the PR")

gh = github.Github(os.environ["GITHUB_TOKEN"])
USER = gh.get_user().login
repo = gh.get_repo("conda-forge/cf-autotick-bot-test-package-feedstock")
pr = repo.create_pull(
    title="[SHOULD NOT BE MERGED] TST test automerge " + BRANCH,
    body=(
        "This PR is an autogenerated test for automerge. It should **NOT** be merged!"),
    head=USER + ":" + BRANCH,
    base=BASE_BRANCH,
    maintainer_can_modify=True,
)
pr.add_to_labels("automerge")


print("\n\n=========================================")
print("adding an extra commit after the label")
subprocess.run(
    "git commit -m 'empty commit' --allow-empty && git push", shell=True, check=True
)
