# .github/workflows-stage

Staging area for GitHub Actions workflows that still need to be moved into
`.github/workflows/`.

A workflow only runs once it lives in `.github/workflows/`. Files here are
inert: GitHub does not read this directory.

## Activating `build-paper.yml`

    mkdir -p .github/workflows
    git mv .github/workflows-stage/build-paper.yml .github/workflows/build-paper.yml
    git commit -m "Move build-paper workflow into .github/workflows"
    git push

Pushing that move requires credentials carrying the `workflow` scope. An SSH
key has it inherently; a personal access token needs the `workflow` box
ticked. Creating the file through the GitHub web UI works too, since the web
UI acts with your own permissions.

Once this directory is empty it can be deleted.

## What `build-paper.yml` does

It compiles `article/SmallLatticeReps.tex` on every push and pull request that
touches `article/`, so that a change to the paper can be checked without a
local LaTeX installation:

- on success, the compiled PDF is attached to the run as a downloadable
  artifact;
- on failure, the LaTeX `.log` and `.blg` files are attached instead, so an
  error can be diagnosed from the browser.

The job drives `article/Makefile` rather than repeating the build steps, so CI
and local builds cannot drift apart. It overrides `PDFLATEX` to add
`-interaction=nonstopmode -halt-on-error`; without those, a LaTeX error would
leave `pdflatex` waiting for keyboard input until the runner times out.
