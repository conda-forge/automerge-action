# How to use this code

1. Change directory to this directory (i.e. `cd scripts`).

2. Clone the repo https://github.com/<username>/cf-autotick-bot-test-package-feedstock.git

3. Clone the upstream repo to `cf-test-master`:

  git clone https://github.com/conda-forge/cf-autotick-bot-test-package-feedstock.git cf-test-master

4. Add the upstream remote

   ```
   cd cf-autotick-bot-test-package-feedstock
   git remote add upstream https://github.com/conda-forge/cf-autotick-bot-test-package-feedstock.git
   cd ..
   ```

5. Run the script `run_tests.sh` feeding it the version number of the test as `vXYZ`
   and your username (e.g., `./run_tests.sh v8`).

6. The script will make a series of PRs. Some should merge and some should not.
