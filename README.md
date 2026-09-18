# fin-lat-rep

Source and supporting material for *Representing Finite Lattices as Congruence
Lattices of Finite Algebras*, by William DeMeo, Ralph Freese and Peter Jipsen.
The LaTeX source of the article is in [`article/`][article].

It asks which finite lattices arise as the congruence lattice of a finite
algebra, and answers it for the small ones: Section 4 tabulates 35 lattices of
at most seven elements and, for 29 of them, a finite unary algebra
B<sub>i</sub> whose congruence lattice is the L<sub>i</sub> drawn beside it.

## Building and checking it

One command sets up everything, and installs nothing into your system:

    nix develop

That shell carries GAP with its Small Groups Library, a JDK, Jython, the
[Universal Algebra Calculator][], TeX Live, Python, `make` and `gh`, pinned by
`flake.lock`, so that everyone builds the paper with the same software.  Then:

    make paper          build article/SmallLatticeReps.pdf
    make uacalc-smoke   check that the calculator comes up (Linux only)
    make help           list every target

`uacalc` opens the calculator on an algebra file and `uacalc-cli` is its Jython
command line, for driving it without a display; both already know where the
jars are.

## What is where

| | |
| --- | --- |
| `article/` | the LaTeX source of the article |
| `lattice-lists/` | Peter Jipsen's catalogs of small lattices and their congruence representations |
| `misc/` | background papers by Aschbacher, Pálfy, and Pálfy and Pudlák |
| `talks/` | slides from talks about this work |
| `programs/` | see [`programs/README.md`](programs/README.md): the GAP programs now live in [UniversalAlgebra/fin-lat-rep-gap][] |
| `uacalc-files/` | see [`uacalc-files/README.md`](uacalc-files/README.md): the algebra files now live in [UACalc/AlgebraFiles][] |

The overalgebras construction is in [williamdemeo/Overalgebras][], and the
closure algorithm, the article's main workhorse, is part of the calculator
itself; see `BasicPartition.java` in [UACalc/uacalcsrc][].

## Contributing

[CONTRIBUTING.md][] has the git workflow, how to add a BibTeX entry, and what
to do when the shell or the LaTeX build misbehaves; the roadmap is
[`docs/GITHUB_PROJECT.md`][plan].  Questions and suggestions are welcome as
[issues][].

[article]: https://github.com/UniversalAlgebra/fin-lat-rep/tree/master/article
[CONTRIBUTING.md]: CONTRIBUTING.md
[plan]: docs/GITHUB_PROJECT.md
[issues]: https://github.com/UniversalAlgebra/fin-lat-rep/issues
[UniversalAlgebra/fin-lat-rep-gap]: https://github.com/UniversalAlgebra/fin-lat-rep-gap
[UACalc/AlgebraFiles]: https://github.com/UACalc/AlgebraFiles
[UACalc/uacalcsrc]: https://github.com/UACalc/uacalcsrc
[williamdemeo/Overalgebras]: https://github.com/williamdemeo/Overalgebras
[Universal Algebra Calculator]: https://uacalc.org
