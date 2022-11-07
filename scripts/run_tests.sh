#!/bin/bash

set -e

export CONDA_SMITHY_LOGLEVEL=DEBUG

pushd cf-autotick-bot-test-package-feedstock

git reset --hard HEAD
git checkout main
git pull upstream main
git pull
git push

python ../move_to_dev_branch.py

python ../make_action_edits.py azure azure $1

python ../make_extra_commit.py azure azure $1

python ../make_no_merge_user.py azure azure $1

python ../make_ci_fail.py azure azure $1
python ../make_prs.py azure azure $1

popd
