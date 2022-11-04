# How to use this code

*REQUIRED*: You must have write access to `conda-forge/cf-autotick-bot-test-package-feedstock`.

1. Change directory to this directory (i.e. `cd scripts`).

2. Fork the feedstock `https://github.com/conda-forge/cf-autotick-bot-test-package-feedstock`

3. Clone your fork `https://github.com/<username>/cf-autotick-bot-test-package-feedstock.git`

4. Clone the upstream repo (`https://github.com/conda-forge/cf-autotick-bot-test-package-feedstock`) to `cf-test-master`:

  ```bash
  git clone https://github.com/conda-forge/cf-autotick-bot-test-package-feedstock.git cf-test-master
  ```

5. Add the upstream remote

   ```bash
   cd cf-autotick-bot-test-package-feedstock
   git remote add upstream https://github.com/conda-forge/cf-autotick-bot-test-package-feedstock.git
   cd ..
   ```

6. Ensure that `conda-smithy` is installed in your active Conda environment.

7. Run the script `run_tests.sh` feeding it the version number of the test as `vXYZ`
   (e.g., `./run_tests.sh v8`).

8. The script will make a series of PRs. Some should merge and some should not.
