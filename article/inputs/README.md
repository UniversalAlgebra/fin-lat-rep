# article/inputs

+  **`macros.sty`**.  The article's macros, including the `lat` node style,
   `\dotsize` and `\hasse`, which every Hasse diagram is drawn with.
+  **`tikz/`**.  Every Hasse diagram, one TikZ pic per file under a header
   the checker reads.  The convention, the header keys, `\hasse`, how to
   compose pics and label vertices from a call site, and how to add a
   lattice are in [`tikz/README.md`](tikz/README.md).
+  **`refs.bib`**.  Generated on every build from the `filecontents*` block
   at the top of `SmallLatticeReps.tex`; never edit or commit it.  See
   CONTRIBUTING.md.
+  **`au.cls`**, **`aschbacher.bib`**, **`AschbacherReviews.pdf`**.  The
   document class and reference material.
