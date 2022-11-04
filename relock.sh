#!/bin/bash

# Regenerate conda-lock.yml

set -e

rm -f conda-lock.yml
conda-lock
