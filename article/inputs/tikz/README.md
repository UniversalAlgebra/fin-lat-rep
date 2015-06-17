# fin-lat-rep/inputs/tikz

This directory contains tikz code that can be used to produces diagrams when
inserted in the main document.

**NOTE:** I have only check a couple of these files to make sure they are really
  ready to be inserted into the document (namely, I checked and fixed
  filter-ideal.tex, parallel-sum.tex, ordinal-sum.tex).
  I will check the others soon and tweak them as necessary. (wjd)  

## Instructions
The most basic way to insert these files into the main LaTeX
source file is by enclosing it in a tikzpicture block, as follows:

    \begin{tikzpicture}
	\input{name-of-tikz-file.tex}
    \end{tikzpicture}

### Diagram resizing and multiple diagrams in one figure.

To get the sizes right, play around with the scale parameter.
To get the spacing between multiple figures right, use the `\hskip` command.
For example, the ordinal sum, parallel sum, and filter+ideal diagrams are all
displayed in the same figure (on page 2 of a recent draft of the paper)
with the following commands (see remarks below):

    \begin{center}
      \begin{figure}[h!]
        \label{fig:ordinal-and-parallel}
        \centering
        \begin{tikzpicture}[scale=0.4]
          \input{inputs/tikz/ordinal-sum.tex}
          \draw (0,-2) node {$L_1$};
          \draw (0,2) node {$L_2$};
        \end{tikzpicture}
        \hskip5mm
        \begin{tikzpicture}[scale=0.4]
          \input{inputs/tikz/parallel-sum.tex}
          \draw (-2,0) node {$L_1$};
          \draw (2,0) node {$L_2$};
        \end{tikzpicture}
        \hskip5mm
        \begin{tikzpicture}[scale=0.4]
          \input{inputs/tikz/filter-ideal.tex}
          \draw (alpha) node [left] {$\alpha$};
          \draw (beta) node [right] {$\beta$};
        \end{tikzpicture}
        \caption{The ordinal (left) and parallel (middle) sum of the lattices
          $L_1$ and $L_2$; a sublattice obtained as a union of a filter
          $\alpha^\uparrow $ and an ideal $\beta^\downarrow$ (right).}
      \end{figure}
    \end{center}

Since the labels on in the diagrams might change depending on the context in
which the diagrams are used, it seems preferable to leave all labels out of the
tikz source code in the inputs/tikz directory and instead include labels in the
calling code, as demostrated above.  In the first two diagrams, the
labels L<sub>1</sub> and L<sub>2</sub> are inserted.  Inserting alpha and beta
in the third diagram uses a different syntax, which is only possible if you
happen to know the names of the nodes in the input file.  (In this case, the
nodes were named alpha and beta in the file filter-ideal.tex.)

Note also the way in which multiple diagrams are included in the same figure.
We must make sure there are no blank lines between \input commands, otherwise
the diagrams will appear one atop another instead of next to each other.  Also,
we can use the hskip command to insert appropriate spacing between diagrams.
