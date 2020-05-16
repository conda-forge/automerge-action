# How to use this code

1. Check out the repo https://github.com/<username>/cf-autotick-bot-test-package-feedstock.git

2. Add the upstream remote

   ```
   cd cf-autotick-bot-test-package-feedstock
   git remote add upstream https://github.com/conda-forge/cf-autotick-bot-test-package-feedstock.git
   cd ..
   ```

2. Run the script `run_tests.sh` feeding it the version number of the test as `vXYZ`
   and your username (e.g., `./run_tests.sh v8 beckermr`).

3. The script will make a series of PRs. Some should merge and some should not.
