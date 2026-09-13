# uacalc-files

**The algebra files have moved to [UACalc/AlgebraFiles][].**  They were
duplicated here and upstream, and the two copies had drifted: the upstream copy
of `SmallLatticeReps.ua` still carried the incorrect B<sub>28</sub> that was
fixed here in [#22][].  Keeping one copy is the way to stop that happening
again.

| Was here | Is now |
| --- | --- |
| `SmallLatticeReps.ua` | [`CongruenceLatReps/SmallLatticeReps.ua`][slr] |
| `Jipsen_congruence_algebras7.ua`, `L7.ua`, `PJ11.ua`, `PJ14.ua`, `A6nseC2.ua`, `alg*.ua` | [`Jipsen/`][jipsen] |
| `GroupsAndGsets/*.ua` | [`Groups/`][groups] |

Three of the files here are upstream under a different name, as follows:
`GroupsAndGsets/A4xA4sdpC2.ua` is `Groups/A4xA4_sdp_C2.ua`;
`GroupsAndGsets/DoubleWinged2x2.ua` is `Groups/PSL2-11_sdp_C2.ua`; and
`GroupsAndGsets/IntransGset-S3ActOnS3-1.ua` is `Groups/RegActS3.ua`, which is
the same pair of operation tables under a name that describes them, since that
action is the regular action of S3 and so transitive, not intransitive.

`SmallLatticeReps.ua` is the file the article means when it refers to the
algebras B<sub>i</sub>.  It holds 29 algebras: B<sub>1</sub> through
B<sub>9</sub>, B4-prime, B<sub>12</sub>, B<sub>13</sub>, B<sub>15</sub>,
B<sub>17</sub>, B<sub>19</sub>, B<sub>21</sub>, and B<sub>23</sub> through
B<sub>35</sub>.  The congruence lattice of each was computed and checked
against the lattice drawn beside it in the article; all 29 agree.

Open these files with the [Universal Algebra Calculator][].

The old files are still in this repository's history.  To get one back, as
follows:

    git show 06cd258:uacalc-files/SmallLatticeReps.ua > SmallLatticeReps.ua

[UACalc/AlgebraFiles]: https://github.com/UACalc/AlgebraFiles
[slr]: https://github.com/UACalc/AlgebraFiles/blob/master/CongruenceLatReps/SmallLatticeReps.ua
[jipsen]: https://github.com/UACalc/AlgebraFiles/tree/master/Jipsen
[groups]: https://github.com/UACalc/AlgebraFiles/tree/master/Groups
[Universal Algebra Calculator]: https://uacalc.org
[#22]: https://github.com/UniversalAlgebra/fin-lat-rep/pull/22
