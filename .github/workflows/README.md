# .github/workflows

+  `build-paper.yml` compiles `article/SmallLatticeReps.tex` on every push and pull
   request that touches `article/`, so that a change to the paper can be checked
   without a local LaTeX installation:

   +  on success, the compiled PDF is attached to the run as a downloadable artifact;
   +  on failure, the LaTeX `.log` and `.blg` files are attached instead, so an error
      can be diagnosed from the browser.

   The job drives `article/Makefile` rather than repeating the build steps, so CI
   and local builds cannot drift apart. It overrides `PDFLATEX` to add
   `-interaction=nonstopmode -halt-on-error`; without those, a LaTeX error would
   leave `pdflatex` waiting for keyboard input until the runner times out.
