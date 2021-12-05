# How to use this code

1. Change directory to this directory (i.e. `cd scripts`).

2. Fork this feedstock `https://github.com/conda-forge/cf-autotick-bot-test-package-feedstock`

3. Clone your fork `https://github.com/<username>/cf-autotick-bot-test-package-feedstock.git`

4. Clone the upstream repo (`https://github.com/conda-forge/cf-autotick-bot-test-package-feedstock`) to `cf-test-master`:

  git clone https://github.com/conda-forge/cf-autotick-bot-test-package-feedstock.git cf-test-master

5. Add the upstream remote

   ```
   cd cf-autotick-bot-test-package-feedstock
   git remote add upstream https://github.com/conda-forge/cf-autotick-bot-test-package-feedstock.git
   cd ..
   ```

6. Run the script `run_tests.sh` feeding it the version number of the test as `vXYZ`
   (e.g., `./run_tests.sh v8`).

7. The script will make a series of PRs. Some should merge and some should not.
