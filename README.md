# Hybrid ML Rescue

Work only in your personal assignment repository. Do not work directly in the course upstream.

## Step 0: bootstrap the course project

```bash
bash bootstrap.sh
```

Expected branch:

```bash
git branch --show-current
# submission
```

Never use these commands on `submission`:

```bash
git reset --hard <older-commit>
git rebase course/base-v3
git push --force
git push --force-with-lease
```

## Stage 1: install Conda/Mamba if needed

Install Miniforge or Mambaforge for Linux x86_64 if `conda` is not available.
Then run:

```bash
bash scripts/doctor.sh bootstrap
```

## Stage 2: create the locked environment

Use the locked package list:

```bash
mamba create -y -n hybridml-rescue --file conda-linux-64.lock
```

If `mamba` is unavailable, use:

```bash
conda create -y -n hybridml-rescue --file conda-linux-64.lock
```

## Stage 3: activate and verify the environment

```bash
conda activate hybridml-rescue
bash scripts/doctor.sh environment
python -m hybridml.environment
```

## Stage 4: build and observe the native failure

```bash
bash scripts/build.sh
```

The first build is expected to fail. Search terms:

```text
CMake imported target
find_package Eigen3
Eigen3 target_link_libraries
```

## Stage 5: repair CMake and C++

Repair the native build files, validate, and commit:

```bash
bash scripts/build.sh

git add CMakeLists.txt cpp/src/fastops.cpp
git commit -m "fix: repair native build"
```

## Stage 6: repair the Python shared-library path

```bash
pytest -q tests/public/test_native.py

git add hybridml/native.py
git commit -m "fix: repair Python native loader"
```

## Stage 7: merge native diagnostics and resolve the one conflict

```bash
git merge --no-ff course/native-integration-v3 -m "merge: integrate native diagnostics"
```

Expected conflicts:

```text
CMakeLists.txt
cpp/src/fastops.cpp
```

Do not use `git checkout --ours .` or `git checkout --theirs .`.
Combine the required lines:

```text
CMakeLists.txt:
- keep the correct Eigen3 target;
- keep FASTOPS_ENABLE_DIAGNOSTICS=1;
- remove all conflict markers.

cpp/src/fastops.cpp:
- keep the plural exported symbol standardize_features;
- keep the non-finite epsilon validation;
- remove all conflict markers.
```

Complete the merge:

```bash
git status
git add CMakeLists.txt cpp/src/fastops.cpp
git commit
```

## Stage 8: cherry-pick deterministic dataset generation

```bash
git cherry-pick course/recovery-data-v3
```

## Stage 9: merge training observability

```bash
git merge --no-ff course/training-observability-v3 -m "merge: integrate training observability"
```

This merge should complete without conflict. Inspect what it introduced:

```bash
git show --stat HEAD
git show HEAD -- config/train.toml
```

## Stage 10: revert the known-bad nondeterministic commit

```bash
git revert --no-edit course/bad-parallel-loader-v3
```

The bad commit and its revert must both remain visible in `git log`.
Do not reset, rebase, or force-push to remove the bad commit.

## Stage 11: build, test, train, and commit the checkpoint

```bash
bash scripts/check.sh
bash scripts/train.sh
python -m hybridml.checkpoint validate artifacts/model.ckpt

git add artifacts/model.ckpt
git commit -m "train: produce reproducible checkpoint"
```

## Stage 12: inspect and push normally

```bash
git log --graph --oneline --decorate --all
python .course/local_check.py history
git push origin submission
```
