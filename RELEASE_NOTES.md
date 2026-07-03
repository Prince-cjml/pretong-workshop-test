# Release Notes

## v3

- Uses Conda/Mamba for Python and native C++ dependencies.
- Provides a documentation-only default branch.
- Distributes fixed release points as immutable `course/*-v3` tags.
- Keeps only two public merge branches for the student workflow.
- Simplifies the required first-parent history to seven commits.
- Keeps one manual conflict-resolution exercise in the native merge.
- Makes the training-observability merge conflict-free and requires a later revert of the known-bad nondeterministic commit.
