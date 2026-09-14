# programs

**The GAP programs have moved to [UniversalAlgebra/fin-lat-rep-gap][],** with
their history.  That repository has a README saying which claim in the article
each program establishes, and all four programs were brought up to date and
verified on GAP 4.15.1.

| Was here | Is now |
| --- | --- |
| `gap/DeMeo/findUpperIntervals.g` | [`findUpperIntervals.g`][fui] |
| `gap/PJ11.gap` | [`PJ11.gap`][pj11] |
| `gap/PJ17.gap` | [`PJ17.gap`][pj17] |
| `gap/Hexagon.g` | [`Hexagon.g`][hex] |
| `gap/Hulpke/Install_new_IntermediateSubgroups_method.gap` | [`obsolete/`][obs], and no longer needed: the method has been in the GAP library since GAP 4.9 |

## What is still here

Neither of the two remaining files is ours.  Both came from Peter Jipsen's
lattice pages, and both are still available there, as follows:

+  `posets.js` draws Hasse diagrams in a browser.  It is by John Snow, with
   modifications by Peter Jipsen, and the current version is at
   <http://math.chapman.edu/~jipsen/posets/posets.js>.
+  `si_lattices92.html` is a saved copy of
   <http://math.chapman.edu/~jipsen/posets/si_lattices92.html>, which lists the
   92 subdirectly irreducible lattices with at most 7 elements.  What was saved
   is the browser's rendering of the page source rather than the page itself,
   so it does not open as a diagram.  Use the live page.

[UniversalAlgebra/fin-lat-rep-gap]: https://github.com/UniversalAlgebra/fin-lat-rep-gap
[fui]: https://github.com/UniversalAlgebra/fin-lat-rep-gap/blob/main/findUpperIntervals.g
[pj11]: https://github.com/UniversalAlgebra/fin-lat-rep-gap/blob/main/PJ11.gap
[pj17]: https://github.com/UniversalAlgebra/fin-lat-rep-gap/blob/main/PJ17.gap
[hex]: https://github.com/UniversalAlgebra/fin-lat-rep-gap/blob/main/Hexagon.g
[obs]: https://github.com/UniversalAlgebra/fin-lat-rep-gap/tree/main/obsolete
