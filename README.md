# fin-lat-rep

<!-- The version badges say what flake.lock pins, the same table `nix develop`
     prints on entry.  Move them when the lock moves.  The license badge names
     the code only, on purpose: LICENSE covers the article and misc/ separately. -->
[![code license: MIT](https://img.shields.io/badge/code%20license-MIT-blue)](LICENSE)
[![paper](https://github.com/UniversalAlgebra/fin-lat-rep/actions/workflows/build-paper.yml/badge.svg)](https://github.com/UniversalAlgebra/fin-lat-rep/actions/workflows/build-paper.yml)
[![Nix flake](https://img.shields.io/badge/Nix-flake-5277C3?logo=nixos&logoColor=white)](flake.nix)
[![GAP 4.15.1](https://img.shields.io/badge/GAP-4.15.1-4b8bbe)](https://www.gap-system.org/)
[![OpenJDK 21](https://img.shields.io/badge/OpenJDK-21-ED8B00?logo=openjdk&logoColor=white)](https://openjdk.org/projects/jdk/21/)
[![Jython 2.7.4](https://img.shields.io/badge/Jython-2.7.4-3776AB)](https://www.jython.org/)
[![Python 3.13](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![TeX Live 2025](https://img.shields.io/badge/TeX%20Live-2025-008080?logo=latex&logoColor=white)](https://tug.org/texlive/)

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

That command lands you in a [Nix][] "devShell" with all the tools you need:
GAP with its Small Groups Library, a JDK, the [Universal Algebra Calculator][],
TeX Live, Jython, Python, `make` and `gh`, all pinned by `flake.lock`, so that
everyone builds the paper with the same software.

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
