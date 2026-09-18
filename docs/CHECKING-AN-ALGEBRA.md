# Checking an algebra by hand

Section 4 of the article tabulates 35 lattices and, for 29 of them, a finite
unary algebra B<sub>i</sub> whose congruence lattice is supposed to be the
lattice L<sub>i</sub> drawn beside it.  This page is how you satisfy yourself
about one of those entries in a couple of minutes.

`make check-catalog` does all 29 at once.  Read that if you want the gate.
This page is the recipe.

## First, what the answer should look like

The catalog is lattices of size **at most** seven, not all of size seven.  Of
the 35, **2 have five elements, 6 have six, and 27 have seven**.  So:

    B1         |A| =  4   |Con(A)| = 5   L1 has 5   ok

is correct and not a shortfall.  L<sub>1</sub> is the pentagon N<sub>5</sub>,
and the article says as much: *"the pentagon, which is typically denoted by
N₅, but in our table in Section 4 we label it L₁"*, together with *"the
smallest algebra that represents N₅ has just four elements"*.  B1 has exactly
four.

The one number that should alarm you is a **`MISMATCH`**, which is what the
defect in [#20] looked like.

## Engine one: this repository's own implementation

No dependencies beyond Python 3.

    cd scripts/python
    PYTHONPATH=. python3 -m finlatrep.check \
        ~/git/UACalc/AlgebraFiles/master/CongruenceLatReps/SmallLatticeReps.ua \
        ../../article/SmallLatticeReps.tex

Real output, trimmed:

    B1         |A| =  4   |Con(A)| = 5   L1 has 5   ok
    B2         |A| =  3   |Con(A)| = 5   L2 has 5   ok
    ...
    B28        |A| = 16   |Con(A)| = 7   L28 has 7   ok
    ...
    All 29 algebras agree with the lattices the article draws.

It computes Con(A) by forming each principal congruence Cg(a, b), the least
congruence identifying a and b, and then join-closing them, since every
congruence of a finite algebra is a join of principal ones.  It reads
L<sub>i</sub> straight out of the TikZ in the article's catalog subsection.

When the two disagree it says so with both covering relations, which is the
form you can actually check against the picture:

    B28        |A| = 16   |Con(A)| = 8   L28 has 7   MISMATCH

      B28 does not represent L28:
        Con(B28) has 8 elements, covers [(1, 0), (2, 1), (3, 2), (4, 3), (5, 4), (6, 0), (7, 5), (7, 6)]
        L28 has 7 elements, covers [(0, 1), (0, 4), (1, 2), (2, 3), (3, 5), (4, 6), (5, 6)]

That is a real run, against
[`scripts/python/fixtures/B28-pre-fix.ua`](../scripts/python/fixtures/B28-pre-fix.ua),
the B28 that stood in AlgebraFiles from 2017 until 2026.  Try it, and try its
counterpart, which must pass:

    PYTHONPATH=. python3 -m finlatrep.check \
        fixtures/B28-pre-fix.ua ../../article/SmallLatticeReps.tex     # exits 1

    PYTHONPATH=. python3 -m finlatrep.check \
        fixtures/B1-B28-correct.ua ../../article/SmallLatticeReps.tex  # exits 0

The two together are what pin the checker in both directions.  With only the
failing one, a checker that called every algebra a mismatch would satisfy the
whole test suite.

## Engine two: UACalc itself

Worth doing when you want a second opinion rather than a second look, because
the article's algebras were produced with UACalc, and an independent
implementation agreeing with it is evidence that neither is wrong.

UACalc has a command line: a Jython layer over its Java API, written by DeMeo
and Freese, in [UACalc/UACalc_CLI] and documented at
[uacalc-at-the-command-line].  The development shell packages it, so from
`nix develop` the recipe is one command with nothing to arrange first:

    uacalc-cli scripts/jython/con_table.py \
        ~/git/UACalc/AlgebraFiles/master/CongruenceLatReps/SmallLatticeReps.ua

`uacalc-cli` is Jython with UACalc's five jars already importable, and it
exports `UACALC_JARS`, which is what `con_table.py` reads.  UACalc's own
`Main-Class` is the Swing application, so the jar alone only gives you the GUI;
the command line is how you reach the same API without a display.

Where those jars come from, since nothing else in the toolchain fetches them:
`flake.nix` pins all five by sha256, `uacalc.jar` from
<https://uacalc.org/uacalc.jar> and `LatDraw.jar`, `groovy-all-1.0.jar`,
`groovy-engine.jar` and `miglayout-3.7-swing.jar` from
[`UACalc/uacalcsrc`]`/jars/` at a pinned commit.

Real output, trimmed, as `<name> <cardinality> <|Con(A)|>`:

    B1 4 5
    B2 3 5
    B3 7 6
    ...
    B28 16 7

Save that table and pass it back to engine one, and the two are compared
outright, on both the cardinality and the number of congruences, so that a
table generated from a stale or different algebra file is caught rather than
read as agreement:

    uacalc-cli scripts/jython/con_table.py \
        ~/git/UACalc/AlgebraFiles/master/CongruenceLatReps/SmallLatticeReps.ua \
        > /tmp/uacalc-table.txt
    make check-catalog UACALC_TABLE=/tmp/uacalc-table.txt

    UACalc agrees on |A| and |Con(A)| for all 29 algebras.
      B1         |A| =  4   |Con(A)| = 5   L1 has 5   ok
      ...
    All 29 algebras agree with the lattices the article draws.

or the same thing from `scripts/python`, if you want the checker directly:

    cd scripts/python
    PYTHONPATH=. python3 -m finlatrep.check --uacalc-table /tmp/uacalc-table.txt \
        ~/git/UACalc/AlgebraFiles/master/CongruenceLatReps/SmallLatticeReps.ua \
        ../../article/SmallLatticeReps.tex

Jython is Python 2, which is why `scripts/jython/` shares no code with
`scripts/python/`.  The table above is the whole interface between them.

## Checking one algebra rather than all of them

Both engines read a `.ua` file, so cut the one algebra you care about into a
file of its own, the way
[`fixtures/B28-pre-fix.ua`](../scripts/python/fixtures/B28-pre-fix.ua) is cut,
and point either engine at that.  The checker compares each algebra `B`*i*
against the lattice `L`*i* the article draws, whatever else is in the file.

Worked, on that one-algebra fixture.  Engine one:

    cd scripts/python
    PYTHONPATH=. python3 -m finlatrep.check \
        fixtures/B28-pre-fix.ua ../../article/SmallLatticeReps.tex

    B28        |A| = 16   |Con(A)| = 8   L28 has 7   MISMATCH

Engine two, on the same file:

    UACALC_JARS=$JARS/uacalc.jar:$JARS/LatDraw.jar:$JARS/groovy-all-1.0.jar:\
    $JARS/groovy-engine.jar:$JARS/miglayout-3.7-swing.jar \
        jython scripts/jython/con_table.py \
            scripts/python/fixtures/B28-pre-fix.ua

    B28 16 8

Both say the same thing: sixteen elements, eight congruences.  L28 has seven,
so this algebra does not represent it.  The corrected counterpart gives

    B1 4 5
    B28 16 7

which is the agreement the catalog should show.

## Why this page exists

B28 was wrong for nine years, from August 2017 until September 2026: six
operations instead of seven, and a congruence lattice with eight elements
rather than L<sub>28</sub>'s seven.  Nobody noticed, because checking meant
doing it by hand and the knowledge of how lived with whoever had last done it.
That is what this page, and the checker beside it, are for.

[#20]: https://github.com/UniversalAlgebra/fin-lat-rep/issues/20
[UACalc/UACalc_CLI]: https://github.com/UACalc/UACalc_CLI
[`UACalc/uacalcsrc`]: https://github.com/UACalc/uacalcsrc
[uacalc-at-the-command-line]: https://universalalgebra.wordpress.com/documentation/uacalc/uacalc-at-the-command-line/
