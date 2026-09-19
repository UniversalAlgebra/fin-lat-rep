# Contributing to fin-lat-rep

## The development shell

    nix develop

is the whole setup story.

Enter that command in the main project directory and (assuming you have Nix
installed) you will be dropped into a [Nix][] devShell with all the tools you need.

The devShell gives you GAP with its Small Groups Library, a JDK, the Universal
Algebra Calculator, TeX Live, Jython, Python with mypy, `make` and `gh`, at the
versions `flake.lock` pins.  It also pins the data the checks read: `$ALGEBRAFILES_DIR`
is the algebras and `$FINLATREPGAP_DIR` the GAP programs, both as flake inputs.

`nix develop .#ci` is the same shell without TeX Live, which is what the
pull-request workflow uses; it saves it the largest download for something it
never runs.  `nix develop .#gap` is GAP and `make` alone, for the slow
workflow, which needs nothing else and should not fail on a UACalc download
it never uses.

Nothing in this repository asks you to install any of them yourself, and nothing
you install yourself is used in preference to the Nix shell's copy.

The flake pins on purpose.  The article cites GAP 4.8.3 from 2016, and on a
current GAP two of the programs behind its group-theoretic claims had silently
stopped establishing them, because they selected subgroups by position in a
list whose order had changed.  See [`docs/GITHUB_PROJECT.md`][plan].

If you don't have Nix installed, you should!  Get it from https://nixos.org/.

If you'd rather not install Nix, you can look at the file `.github/workflows/build-paper.yml`
which lists the Debian packages the article needs.  You can then install matching
versions by hand (but that is what Nix is for).

## Building the article

    make paper

runs `article/Makefile`, which is pdflatex, bibtex, pdflatex, pdflatex.  The
result, `article/SmallLatticeReps.pdf`, is a build product and is not
committed.  CI builds the same file on every push that touches `article/`.

    make gallery

draws every Hasse diagram side by side, one per file under
`article/inputs/tikz/`, into `article/inputs/tikz/gallery.pdf`, also a build
product.  The diagrams are TikZ pics, one per lattice, under a header the
catalog check reads; [`article/inputs/tikz/README.md`][tikz] says how to add
one.

## Adding a reference

References live in the `filecontents*` block at the top of
`article/SmallLatticeReps.tex`, between `\begin{filecontents*}{inputs/refs.bib}`
and `\end{filecontents*}`.  Add your entry there.

**Never add an entry to `article/inputs/refs.bib`**.  That file is generated
from the block above on every build: `article/Makefile` deletes it before each
run, and `.gitignore` excludes it, so an entry put there is lost the next time
anybody builds the paper.

## Driving the calculator

`uacalc` opens the GUI on a `.ua` file.  `uacalc-cli` is the Jython command
line DeMeo and Freese wrote, documented at [uacalc-at-the-command-line][]:
given a script it runs it, given nothing it is a Python 2 prompt with UACalc
importable.

    $ uacalc-cli
    >>> from org.uacalc.io import AlgebraIO
    >>> algs = AlgebraIO.readAlgebraListFile("CongruenceLatReps/SmallLatticeReps.ua")
    >>> for a in algs[:3]: print a.getName(), a.cardinality(), a.con().cardinality()
    B1 4 5
    B2 3 5
    B3 7 6

The wrapper sets `JYTHONPATH`, `CLASSPATH` and `UACALC_JARS` to the same five
jars, so there is nothing to arrange by hand.  The algebras are in
[UACalc/AlgebraFiles][], which the flake pins too: the shell sets
`$ALGEBRAFILES_DIR` to that pinned copy, which is what `make check-catalog`
reads when you do not say otherwise, and `nix flake update algebrafiles` is how
it moves.  The GAP programs in [UniversalAlgebra/fin-lat-rep-gap][] are pinned
the same way, as `$FINLATREPGAP_DIR`, moved by `nix flake update finlatrepgap`.

The [Scala REPL][scala-repl], `scala -classpath uacalc.jar`, is the exploratory
path only: it is documented for interactive use, with no scripted invocation
and no example of loading a `.ua` file, and the Scala it was written against is
from 2013.  Anything that has to be re-run belongs in `uacalc-cli`.

## Verifying a change

    make verify

runs every computational check that gates a change, and is one of the two jobs
CI runs on a pull request (`.github/workflows/verify.yml`).  In order, it does
the following:

+  `make typecheck`, `mypy --strict` over `scripts/python`, which runs nothing
   and takes about a second, so a type error stops the run before anything
   slower starts;
+  `make test`, the unit suites under `scripts/python`;
+  `make uacalc-table`, which has UACalc itself compute |Con(A)| for every
   algebra in the pinned `.ua` file, writing `build/uacalc-table.txt`;
+  `make check-catalog` against that table, so the Python checker and UACalc
   must agree with each other and with the lattice the article draws beside
   each algebra;
+  `make verify-gap`, which re-runs the fast GAP programs (`PJ17.gap`,
   `PJ11.gap`) from the pinned fin-lat-rep-gap and asserts the numbers the
   article states, through `scripts/gap/verify-fast.g`.

About a minute all told, most of it GAP.  Each step runs on its own too, and
`make help` lists them.

Every check prints one line: a mark, the file that ran it, and what it tested,
as follows:

    ✅ mypy --strict  finlatrep and _utils annotate every function and value
    ✅ finlatrep/test_ua.py  a short table is rejected
    ✅ finlatrep/check.py  B28        |A| = 16   |Con(A)| = 7   L28 has 7
    ✅ verify-fast.g  [G:H] = 36

A failing check prints ❌ instead, with its detail after the suite, and each
stage ends with a marked summary; `make verify` ends with one of its own.  The
unit tests get their line from `_utils/run_tests.py`, which prints the first
sentence of the test's docstring, or its name in words when it has none, so a
well-named test is a well-described one.

The other CI job is

    nix flake check

which evaluates every flake output and runs the UACalc smoke test under a
virtual framebuffer.  It is not folded into `make verify` because every Make
target here runs without Nix, and the two answer different questions: `verify`
asks whether the mathematics still holds, `nix flake check` whether the
environment still builds.  Run it yourself after touching `flake.nix` or
`flake.lock`.

    make verify-slow

is the rest: `Hexagon.g` and `pentagonSearch.g`, which take minutes and several
gigabytes.  It does not gate pull requests; `.github/workflows/verify-slow.yml`
runs it weekly, on demand, and whenever `flake.lock` changes, and on failure
opens (or comments on) one issue titled "Scheduled verification failed".  A GAP
upgrade is what it exists to catch; see Remark 3.7 of the article for the last
time that happened.

When a GAP assertion fails, the driver prints a ❌ line naming the assertion,
then the value it got and the value it wanted, for each one, and exits 1.  A changed number
is not necessarily a wrong number: first decide whether GAP or the article is
right, then fix the one that is wrong, and only then the assertion.

## The git workflow

Branch from the issue.  The "Create a branch" button on an issue's page names
the branch after it and tells you how to fetch it, which keeps the branch, the
issue and the pull request tied together with no naming convention to remember.
For issue #26 it produced `26-m1-2-package-uacalc-in-the-flake`.

    git fetch origin
    git switch <the branch that button made>

Commit, push, and open a pull request whose description ends with `Closes #N`,
naming your own issue, as a paragraph of its own, which is the form GitHub's
auto-close parser recognizes.  Leave that description unwrapped: GitHub renders
every newline in a pull request body as a line break, so a hard-wrapped one
displays ragged.  Commit messages are the opposite, and wrap at about 80
columns.

## Emacs and magit

The instructions that used to be here installed magit from marmalade, a package
archive that no longer exists.  Magit is in MELPA and in most distributions,
`M-x magit-status` is the whole entry point, and its manual is at
<https://magit.vc/manual/>.

## The project plan

[`docs/GITHUB_PROJECT.md`][plan] is the roadmap.  Structure lives in the file;
state (issue numbers, whether an issue is open, who holds it) lives on GitHub,
and the regions between `BEGIN GENERATED` and `END GENERATED` markers are
rewritten from GitHub rather than edited by hand.

    make project-lint           check the file, offline
    make project-update         rewrite the generated regions from GitHub
    make project-update-check   fail if the file and GitHub disagree
    make project-populate-dry   preview what populate would create
    make project-populate       create the labels, milestones and issues

The engine is [williamdemeo/github-project][], a flake input, never a copy in
this repository; `nix flake update github-project` upgrades it deliberately,
and `GHPROJECT_DIR=<checkout> make project-lint` runs a local one instead.

## When something goes wrong

**A change to a new file seems to have no effect, or Nix cannot see it**.  A
flake sees only files git knows about, so an untracked file is simply absent
from the tree Nix builds from.  `git add` it first; you do not have to commit.

**`! LaTeX Error: File 'x.sty' not found`**.  The shell's TeX Live is named
package by package rather than by collection, because the collections come to
3794 MiB against this list's 441 MiB.  Add the package that owns the file to
the list in `flake.nix`; the comment above that list gives the one-liner that
asks TeX Live's own database which package that is, since the owner is rarely
the name you would guess.

**`acro:` keys in the margins of your PDF**.  Not an error, and not yours.  The
article loads `showkeys`, and TeX Live 2025's `acronym` is caught by it where
TeX Live 2023's was not, so a local build shows sixteen keys that the CI
artifact does not.

**`hash mismatch in fixed-output derivation` for `uacalc.jar`**.  The file
behind <https://uacalc.org/uacalc.jar> has changed; the URL carries no version,
so the hash is what turns that into a loud failure instead of a silent change
of environment.  The comment beside the package in `flake.nix` says what to do.

**`ImportError: No module named uacalc`**.  You are running plain `jython` with
`CLASSPATH` set.  nixpkgs runs Jython as `java -jar jython.jar`, and `java
-jar` ignores both `-cp` and `CLASSPATH`.  Use `uacalc-cli`, or set
`JYTHONPATH`.

**A `make project-*` target fails with status 2**.  That is a failed run, most
often `gh` not being authenticated; check with `gh auth status`.  Status 1 from
`project-update-check` is a different thing: it means the file and GitHub
disagree, and `make project-update` is the fix.

[plan]: docs/GITHUB_PROJECT.md
[tikz]: article/inputs/tikz/README.md
[UACalc/AlgebraFiles]: https://github.com/UACalc/AlgebraFiles
[UniversalAlgebra/fin-lat-rep-gap]: https://github.com/UniversalAlgebra/fin-lat-rep-gap
[williamdemeo/github-project]: https://github.com/williamdemeo/github-project
[uacalc-at-the-command-line]: https://universalalgebra.wordpress.com/documentation/uacalc/uacalc-at-the-command-line/
[scala-repl]: https://universalalgebra.wordpress.com/documentation/scala/scala-repl-with-uacalc-objects/
[Nix]: https://nixos.org/
