# fin-lat-rep

Source and supporting material for *Representing Finite Lattices as Congruence
Lattices of Finite Algebras*, by William DeMeo, Ralph Freese and Peter Jipsen.
The LaTeX source of the article is in [`article/`][article].

It asks which finite lattices are congruence lattices of finite algebras, and
answers it for the small ones: Section 4 tabulates 35 lattices of at most seven
elements and, for 29 of them, a unary algebra representing each one.

## Building and checking it

These instructions assume you have [Nix][] installed and you know how to use
the command line in a terminal.  If you don't have Nix, go to https://nixos.org/
and install it.

One command sets up everything, and installs nothing permanently on your system:

    nix develop

That command lands you in a [Nix][] "devShell" with all the tools you need: GAP with its Small Groups Library, a JDK, the [Universal
GAP with its Small Groups Library, a JDK, the [Universal
Algebra Calculator][], TeX Live, Jython, Python, `make` and `gh`, all pinned by
`flake.lock`, so that everyone builds the paper with the same software.

Once you're in the devShell,

    make paper          build article/SmallLatticeReps.pdf
    make check-catalog  check every algebra against the lattice drawn beside it
    make uacalc-smoke   check that the calculator comes up (Linux only)
    make help           list every target

`uacalc` opens the calculator on an algebra file, `uacalc-cli` is its Jython
command line, and [`docs/CHECKING-AN-ALGEBRA.md`][checking] is how to satisfy
yourself about a single algebra by hand, in either engine.

## What is where

| | |
| --- | --- |
| `article/` | the LaTeX source of the article |
| `lattice-lists/` | Peter Jipsen's catalogs of small lattices and their congruence representations |
| `misc/` | background papers by Aschbacher, Pálfy, and Pálfy and Pudlák |
| `talks/` | slides from talks about this work |
| `programs/` | see [`programs/README.md`](programs/README.md): the GAP programs now live in [UniversalAlgebra/fin-lat-rep-gap][] |
| `uacalc-files/` | see [`uacalc-files/README.md`](uacalc-files/README.md): the algebra files now live in [UACalc/AlgebraFiles][] |

The overalgebras construction is in [williamdemeo/Overalgebras][]; the closure
algorithm, the article's workhorse, is `BasicPartition.java` in
[UACalc/uacalcsrc][].

## Contributing

[CONTRIBUTING.md][] has the git workflow, how to add a BibTeX entry, and what
to do when the shell or the LaTeX build misbehaves; the roadmap is
[`docs/GITHUB_PROJECT.md`][plan].  Questions and suggestions are welcome as
[issues][].

[article]: https://github.com/UniversalAlgebra/fin-lat-rep/tree/master/article
[CONTRIBUTING.md]: CONTRIBUTING.md
[plan]: docs/GITHUB_PROJECT.md
[checking]: docs/CHECKING-AN-ALGEBRA.md
[issues]: https://github.com/UniversalAlgebra/fin-lat-rep/issues
[UniversalAlgebra/fin-lat-rep-gap]: https://github.com/UniversalAlgebra/fin-lat-rep-gap
[UACalc/AlgebraFiles]: https://github.com/UACalc/AlgebraFiles
[UACalc/uacalcsrc]: https://github.com/UACalc/uacalcsrc
[williamdemeo/Overalgebras]: https://github.com/williamdemeo/Overalgebras
[Universal Algebra Calculator]: https://uacalc.org
[Nix]: https://nixos.org/
