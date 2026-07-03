from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

BASE = "course/base-v3"
START = "course/broken-start-v3"
NATIVE_TIP = "course/native-integration-v3"
TRAINING_TIP = "course/training-observability-v3"
BAD_COMMIT = "course/bad-parallel-loader-v3"
RECOVERY = "course/recovery-data-v3"
IMMUTABLE = "course/immutable-v3"

EXPECTED_SUBJECTS = [
    "fix: repair native build",
    "fix: repair Python native loader",
    "merge: integrate native diagnostics",
    "feat: deterministic repository dataset",
    "merge: integrate training observability",
    'Revert "perf: enable nondeterministic data loading"',
    "train: produce reproducible checkpoint",
]

PATH_POLICY = {
    "fix: repair native build": {"CMakeLists.txt", "cpp/src/fastops.cpp"},
    "fix: repair Python native loader": {"hybridml/native.py"},
    "merge: integrate native diagnostics": {"CMakeLists.txt", "cpp/src/fastops.cpp"},
    "feat: deterministic repository dataset": {"hybridml/data.py"},
    "merge: integrate training observability": {"hybridml/train.py", "config/train.toml"},
    'Revert "perf: enable nondeterministic data loading"': {"config/train.toml"},
    "train: produce reproducible checkpoint": {"artifacts/model.ckpt"},
}

PROTECTED_PATHS = [
    "PROJECT_SPEC.md",
    "environment.yml",
    "conda-linux-64.lock",
    ".condarc",
    "pyproject.toml",
    "CMakePresets.json",
    "cpp/include/fastops.h",
    "hybridml/environment.py",
    "hybridml/model.py",
    "hybridml/checkpoint.py",
    "hybridml/fingerprint.py",
    "scripts/doctor.sh",
    "scripts/check.sh",
    "tests/public",
    ".course",
    ".github/workflows",
    "bootstrap.sh",
]

ALLOWED_FROM_START = set().union(*PATH_POLICY.values())


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def require_ancestor(ancestor: str, descendant: str = "HEAD") -> None:
    result = subprocess.run(["git", "merge-base", "--is-ancestor", ancestor, descendant], check=False)
    require(result.returncode == 0, f"{ancestor} is not an ancestor of {descendant}.")


def parents(commit: str) -> list[str]:
    return git("show", "-s", "--format=%P", commit).split()


def diff_names(a: str, b: str) -> set[str]:
    output = git("diff", "--name-only", "--no-renames", a, b)
    return {line for line in output.splitlines() if line}


def changed_after_start() -> set[str]:
    return diff_names(START, "HEAD")


def preflight() -> None:
    missing = []
    for ref in (BASE, START, NATIVE_TIP, TRAINING_TIP, BAD_COMMIT, RECOVERY, IMMUTABLE):
        result = subprocess.run(["git", "rev-parse", "--verify", f"{ref}^{{commit}}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if result.returncode != 0:
            missing.append(ref)
    require(not missing, "Missing trusted course refs:\n" + "\n".join(missing))
    print("preflight passed")


def hygiene() -> None:
    unexpected = changed_after_start() - ALLOWED_FROM_START
    require(not unexpected, "Unexpected paths modified:\n" + "\n".join(sorted(unexpected)))
    tracked = git("ls-files").splitlines()
    forbidden_suffixes = (".so", ".o", ".a")
    binaries = [p for p in tracked if p.endswith(forbidden_suffixes)]
    require(not binaries, "Compiled binary artifacts must not be tracked:\n" + "\n".join(binaries))
    root = Path.cwd().resolve()
    total = 0
    for path in tracked:
        p = Path(path)
        if p.is_symlink():
            resolved = p.resolve()
            require(root in resolved.parents or resolved == root, f"Symlink escapes repository: {path}")
        if p.is_file():
            data = p.read_bytes()
            total += len(data)
            require(len(data) <= 2_000_000, f"Tracked file too large: {path}")
            if data.startswith(b"version https://git-lfs.github.com/spec"):
                raise SystemExit(f"Git LFS pointer is not allowed: {path}")
    require(total <= 10_000_000, "Tracked repository content exceeds 10 MB.")
    for bad in ("build", ".pytest_cache", "__pycache__"):
        require(not Path(bad).exists(), f"Generated directory is present: {bad}")
    print("repository hygiene passed")


def protected_paths() -> None:
    for path in PROTECTED_PATHS:
        result = subprocess.run(["git", "diff", "--no-ext-diff", "--no-renames", "--exit-code", IMMUTABLE, "HEAD", "--", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        require(result.returncode == 0, f"Protected path changed: {path}")
    print("protected paths passed")


def patch_id(commit: str, path: str) -> str:
    show = subprocess.Popen(["git", "show", "--format=", commit, "--", path], stdout=subprocess.PIPE, text=True)
    return subprocess.check_output(["git", "patch-id", "--stable"], stdin=show.stdout, text=True).split()[0]


def history() -> None:
    preflight()
    for required in (START, NATIVE_TIP, TRAINING_TIP, BAD_COMMIT):
        require_ancestor(required)
    commits = git("rev-list", "--first-parent", "--reverse", f"{START}..HEAD").splitlines()
    subjects = [git("show", "-s", "--format=%s", commit) for commit in commits]
    require(subjects == EXPECTED_SUBJECTS, "First-parent subjects do not match the v3 contract.")

    for commit, subject in zip(commits, subjects):
        changed = diff_names(f"{commit}^1", commit)
        allowed = PATH_POLICY[subject]
        require(changed <= allowed, f"{subject} changed unexpected paths: {sorted(changed - allowed)}")
        protected_touched = changed & set(PROTECTED_PATHS)
        require(not protected_touched, f"{subject} touched protected paths: {sorted(protected_touched)}")

    native_merge = commits[2]
    training_merge = commits[4]
    revert_commit = commits[5]
    require(len(parents(native_merge)) == 2, "Native integration commit is not a two-parent merge.")
    require(parents(native_merge)[1] == git("rev-parse", f"{NATIVE_TIP}^{{commit}}"), "Wrong native merge second parent.")
    require(len(parents(training_merge)) == 2, "Training integration commit is not a two-parent merge.")
    require(parents(training_merge)[1] == git("rev-parse", f"{TRAINING_TIP}^{{commit}}"), "Wrong training merge second parent.")
    require(len(parents(revert_commit)) == 1, "Required revert must be a normal one-parent commit.")
    require_ancestor(BAD_COMMIT, f"{revert_commit}^")
    require(patch_id(RECOVERY, "hybridml/data.py") == patch_id(commits[3], "hybridml/data.py"), "Recovery patch identity does not match.")
    bad_paths = diff_names(f"{BAD_COMMIT}^", BAD_COMMIT)
    revert_paths = diff_names(f"{revert_commit}^", revert_commit)
    require(revert_paths == bad_paths == {"config/train.toml"}, "Revert paths do not match the bad commit.")
    config = git("show", f"{revert_commit}:config/train.toml")
    require("num_threads = 1" in config and "deterministic = true" in config, "Revert did not restore deterministic config.")
    print("git history passed")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["preflight", "protected", "hygiene", "history"])
    args = parser.parse_args()
    if args.command == "preflight":
        preflight()
    elif args.command == "protected":
        protected_paths()
    elif args.command == "hygiene":
        hygiene()
    else:
        history()


if __name__ == "__main__":
    main()
