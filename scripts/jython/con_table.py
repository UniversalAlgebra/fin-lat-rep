"""
File: scripts/jython/con_table.py

Description: Compute |Con(A)| for every algebra in a .ua file, using UACalc.

  This is the second opinion.  The Python 3 checker under scripts/python/
  computes congruence lattices itself; this drives the Universal Algebra
  Calculator, the program the article's algebras were made with, and emits a
  table the Python 3 side can compare against.

  It is Python 2, because Jython is, and so it deliberately shares no code
  with scripts/python/.  It sits in scripts/jython/ rather than under
  scripts/python/ for that reason: the Python 3 tree is type-annotated and
  test-discovered as a unit, and a module that can only be imported by a
  Jython interpreter has no business inside it.  Its pure helpers are still
  tested, from scripts/python/finlatrep/test_con_table.py, which loads this
  file by path.

  The interface between the two sides is this table, one algebra per line:

      <algebra name> <cardinality> <|Con(A)|>

  Usage.  Point UACALC_JARS at the jars, colon separated, and run:

      UACALC_JARS=/path/uacalc.jar:/path/LatDraw.jar:/path/groovy-all-1.0.jar:\
      /path/groovy-engine.jar:/path/miglayout-3.7-swing.jar \
          jython scripts/jython/con_table.py SmallLatticeReps.ua

  The jars go on sys.path here rather than relying on CLASSPATH, because a
  packaged jython wrapper does not necessarily pass that environment variable
  through to the JVM, and the failure when it does not is an ImportError that
  looks like a missing UACalc rather than a missing classpath.

  See docs/CHECKING-AN-ALGEBRA.md for where the jars come from.
"""

import os
import sys


def add_jars_to_path(jars):
    """Put each jar on sys.path so Jython can import from it."""
    for jar in jars:
        if jar and jar not in sys.path:
            sys.path.append(jar)


def con_table(path):
    """Yield (name, cardinality, |Con(A)|) for each algebra in the file."""
    from org.uacalc.io import AlgebraIO

    for algebra in AlgebraIO.readAlgebraListFile(path):
        yield (algebra.getName(), algebra.cardinality(), algebra.con().cardinality())


def main(argv):
    """Print the table.  Nothing below this function prints."""
    if len(argv) != 2:
        sys.stderr.write("usage: jython con_table.py <file.ua>\n")
        return 2
    jars = os.environ.get("UACALC_JARS", "")
    if not jars:
        sys.stderr.write(
            "error: set UACALC_JARS to the UACalc jars, colon separated.\n"
            "       See docs/CHECKING-AN-ALGEBRA.md.\n"
        )
        return 2
    add_jars_to_path(jars.split(os.pathsep))
    try:
        rows = list(con_table(argv[1]))
    except ImportError:
        sys.stderr.write(
            "error: UACalc is not importable from UACALC_JARS=%s\n" % jars
        )
        return 2
    for name, cardinality, con_size in rows:
        print("%s %d %d" % (name, cardinality, con_size))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
