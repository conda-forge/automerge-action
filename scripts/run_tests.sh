#!/bin/bash

set -e

export CONDA_SMITHY_LOGLEVEL=DEBUG

# run this section only if these branches on master somehow get removed
# pushd cf-test-master
# for linux in circle travis azure; do
#   for osx in circle travis azure; do
#     git co master
#     git co -b ${linux}-${osx}
#     git push --set-upstream origin ${linux}-${osx}
#   done
# done
# popd

pushd cf-autotick-bot-test-package-feedstock

python ../make_no_merge_user.py azure azure $1 $2

python ../make_no_linter.py azure azure $1 $2

for linux in travis azure circle; do
  python ../make_ci_fail.py circle ${linux} $1 $2
  for osx in azure; do
    python ../make_prs.py ${linux} ${osx} $1 $2
  done
done

python ../make_prs.py circle circle $1 $2
