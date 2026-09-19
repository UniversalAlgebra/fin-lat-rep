# Hasse diagrams

Every lattice the article draws lives here, one file per lattice, each file a
TikZ pic in one shape under one header.  The catalog's thirty-five lattices
are `L1.tex` to `L35.tex`, numbered as the article numbers them; the rest have
descriptive names.  `all.tex` inputs every file once, from the article's
preamble, and `gallery.tex` draws every file side by side (`make gallery`).

The checker that gates every pull request, `scripts/python/finlatrep/`, reads
these files: for each catalog lattice it compares the algebra's congruence
lattice, the drawing, and the `covers:` line of the header, pairwise.  So the
header is not decoration.  It is what makes a diagram checkable.

## The shape of a file

`L6.tex`, the hexagon, is the whole convention:

    % id: L6
    % aliases: hexagon, 2015-file: L6
    % elements: 6
    % covers: 0<1 0<3 1<2 3<4 2<5 4<5
    % represented-by: B6 (SmallLatticeReps.ua)
    % tags: nonmodular, self-dual
    \tikzset{L6/.pic={
      \node[lat] (0) at (0,0) {};
      \node[lat] (1) at (-1,1) {};
      \node[lat] (3) at (1,1) {};
      \node[lat] (2) at (-1,2) {};
      \node[lat] (4) at (1,2) {};
      \node[lat] (5) at (0,3) {};
      \draw (0) -- (1);
      \draw (0) -- (3);
      \draw (1) -- (2);
      \draw (3) -- (4);
      \draw (2) -- (5);
      \draw (4) -- (5);
    }}

The rules, which the checker holds a file to, are as follows:

+  **One pic per file, named after the file**.  `L6.tex` defines the pic `L6`
   and the header says `id: L6`.
+  **Vertices are `\node[lat] (name) at (x,y) {};`, one per line**.  Names may
   be numbers or words (`bottom`, `n11`, `left-low`); the checker accepts
   `[\w-]+`.  `lat` is the one node style, defined in `../macros.sty` with the
   one dot size, `\dotsize`.
+  **Covering edges are `\draw (a) -- (b);`, one per line**.  Which end is the
   lower one is read off the y coordinates, never off the order the ends are
   written in, so two vertices joined by an edge must not sit at the same
   height.  No chains (`(a) -- (b) -- (c)`), no `to`, no options.
+  **Nodes and edges only**.  No labels, no text, no `\draw` of anything but
   an edge.  Labels belong at the call site, which knows what the picture is
   for; see below.
+  **The bottom element is at the origin**, and the picture is three units
   tall.  When the longest chain has three covers, which is most of the
   catalog, that is unit spacing between levels; a lattice with a longer or
   shorter chain is drawn to the same height, so that one scale gives one
   height across the catalog.  This is the convention the hand-drawn 2015
   files already followed (`L7.tex` compresses a chain of four covers into
   three units), and the catalog's own coordinates, Peter Jipsen's, were
   multiplied by 1.5 and shifted to meet it.
+  **No `%` inside the pic body**.  The checker strips comments by backslash
   parity before reading, so a commented-out edge is not drawn, but a diagram
   is easier to trust when there is nothing to strip.

The reader knows only the two forms above and ignores every other line.  That
is safe precisely because of the header: a vertex or edge written any other
way is lost, the drawing then disagrees with `covers:`, and `make verify`
says so.

## The header

Six keys, fixed, one `% key: value` line each, in this order.  A line of that
form with any other key is an error, so that a misspelt `cover:` cannot
silently drop the check.  A comment line at the top of the file that is not
of that form is free text and is ignored.

+  **`id`**.  The pic's name, which is the file's name without `.tex`.
+  **`aliases`**.  Other names the lattice goes by, comma separated, and the
   name the file had in 2015 as `2015-file: NAME` where the two differ.  May
   be empty.
+  **`elements`**.  The number of vertices.  Checked against the drawing.
+  **`covers`**.  The covering relation as `lower<upper` pairs separated by
   spaces, in the vertex names of the drawing.  Checked against the drawing
   for equality and against the algebra's congruence lattice for isomorphism.
+  **`represented-by`**.  The algebra in `SmallLatticeReps.ua` whose
   congruence lattice this is, as `B6 (SmallLatticeReps.ua)`, or where the
   representation is known from otherwise, or `none known`.
+  **`tags`**.  Comma separated.  Today: `modular` or `nonmodular`,
   `distributive` where it holds, `self-dual` or `dual-of-L<k>` for the
   catalog's dual pairs, and a few words where a file needs them (`labelled`,
   `alternative layout of L13`).

A file that draws something that is not a lattice, the potato diagrams of the
closure-properties figures, carries only `id`, `aliases` and `tags`, with the
tag `schematic`; it has no `covers:` and the checker does not read it.

The header is the seed of a database.  It is greppable today
(`grep '^% covers:' *.tex`) and can be harvested into JSON by a short script
tomorrow; when the collection outgrows hand-written TikZ, the record becomes
the source and the `.tex` file becomes generated output, with the same file
name and the same call in the manuscript.

## Drawing one: `\hasse`

    \hasse{L6}          % the catalog's scale, 0.4: a diagram 1.2cm tall
    \hasse[1]{L6}       % a figure of a single lattice
    \hasse[0.8]{L6}     % a wide figure

`\hasse[scale]{name}` is defined in `../macros.sty`: a `tikzpicture` holding
`\pic[scale=...]{name}`, its baseline centered so that it sits level with a
label or a table beside it, and a millimetre of margin above and below so
that the catalog's rows do not touch.  The scale set is 0.4, 0.8, and 1; the
composite figures below use 0.3, 0.35 and 0.4 for the schematics.  `scale=` scales
positions and not dots or line widths, which is why the dot size is one macro
and why one scale per context matters.

## Composing pics and labelling vertices

A figure that needs labels, or more than one lattice, writes its own
`tikzpicture` and places pics.  Two things to know, both measured on
pgf 3.1.11a:

+  **The scale goes on the pic**.  TikZ places a pic like a node: a picture's
   `scale=` moves the pic without scaling what it draws.  Give the pic the
   scale, and give the picture the same scale so that coordinates written at
   the call site (a label at `(0,-2)`) land where the pic's vertices are:

        \begin{tikzpicture}[scale=0.4]
          \pic[scale=0.4]{ordinal-sum};
          \draw (0,-2) node {$L_1$};
          \draw (0,2) node {$L_2$};
        \end{tikzpicture}

+  **A named pic prefixes its vertices with its name, verbatim**.  After
   `\pic (l) {L11};` the top is `(ltop)`, so name the pic with a trailing
   hyphen and read the vertices as `(l-top)`:

        \begin{tikzpicture}
          \pic (l-) {L11};
          \draw (l-top) node [above] {$G$};
          \draw (l-mp) node [left] {$\alpha$};
        \end{tikzpicture}

   An unnamed pic leaves its vertex names bare, which works for one pic and
   collides for two.

Two pics compose in one picture the same way: `\pic[scale=0.5] at (2,0) {L6};`
places a second one.  The article's Figure 9 draws `L11` and
`L11-upper-interval` side by side with their vertices labelled, and Figure 2
places three schematics; both are in `SmallLatticeReps.tex`.

## Adding a lattice

1.  Write `NAME.tex` in the shape above, with its header; for a catalog
    lattice the name is `L<i>` and nothing else, since that is how the
    checker finds the file from the label $\mathbf{L}_i$.
2.  Add `\input{inputs/tikz/NAME.tex}` to `all.tex`, in order, and
    `\entry{NAME}` to `gallery.tex`.  `make test` fails on a file missing
    from either, which is what stops a new lattice compiling to nothing.
3.  Draw it: `\hasse{NAME}` in the catalog, or a `tikzpicture` in a figure.
4.  Run `make verify`.  For a catalog lattice with an algebra, the line
    `✅ finlatrep/check.py  B6  |A| = 6  |Con(A)| = 6  L6 has 6` says the
    algebra, the drawing and the header agree; the line before it says every
    file agrees with its own header.  Then `make paper` and `make gallery`,
    and look.

## What is here besides the catalog

+  `L8-alt`, `L13-alt`, `L17-alt`, `L20-alt`: the 2015 hand drawings of L8
   (as M4), L13, L17 and L20, in layouts that differ from the catalog's, kept
   until it is decided whether the paper wants them.
+  `L11-upper-interval`: the pentagon laid out as it sits in L11, for the
   right-hand picture of Figure 9.  It is the lattice L1 in another layout,
   the one place a lattice has two files.
+  `two-by-two`: the four-element Boolean lattice of Figure 1.
+  `shareshian`: the fourteen-element lattice of Figure 8.
+  `N54W`, `wheatstone-bridge`: 2015 files the article does not use, kept
   with their labels inside (tagged `labelled`) until decided.
+  `ordinal-sum`, `parallel-sum`, `filter-ideal`, `general-ordinal-sum`,
   `adjoined-ordinal-sum`: the schematics of Figures 2 and 4.
