<?xml version="1.0"?>
<!-- B1 and B28 as they stand in UACalc/AlgebraFiles after the correction
     of fin-lat-rep #22.  The catalog check must PASS on this file.

     Its counterpart B28-pre-fix.ua must FAIL, and together the two pin both
     directions: without a passing case a checker that called every algebra a
     mismatch would satisfy the whole suite.

     B1 is here because its congruence lattice is the pentagon, five elements
     rather than seven, which is the answer that looks wrong and is not.
     B28 is the algebra the regression is about.

     This file's sha256 is pinned in scripts/python/finlatrep/test_check.py. -->
<algebraList>
<algebra>
  <basicAlgebra>
    <algName>B1</algName>
    <desc>Representations as congruence lattices of most algebras of at most 7 elements.</desc>
    <cardinality>4</cardinality>
    <operations>
      <op>
        <opSymbol>
          <opName>h0</opName>
          <arity>1</arity>
        </opSymbol>
        <opTable>
          <intArray>
            <row>1, 0, 3, 2</row>
          </intArray>
        </opTable>
      </op>
      <op>
        <opSymbol>
          <opName>h1</opName>
          <arity>1</arity>
        </opSymbol>
        <opTable>
          <intArray>
            <row>1, 0, 1, 0</row>
          </intArray>
        </opTable>
      </op>
    </operations>
  </basicAlgebra>
</algebra>
<algebra>
  <basicAlgebra>
    <algName>B28</algName>
    <desc>A correct version representing L28</desc>
    <cardinality>16</cardinality>
    <operations>
      <op>
        <opSymbol>
          <opName>e0</opName>
          <arity>1</arity>
        </opSymbol>
        <opTable>
          <intArray>
            <row>0,1,2,3,4,5,1,2,3,4,5,0,1,3,4,5</row>
          </intArray>
        </opTable>
      </op>
      <op>
        <opSymbol>
          <opName>e1</opName>
          <arity>1</arity>
        </opSymbol>
        <opTable>
          <intArray>
            <row>0,6,7,8,9,10,6,7,8,9,10,0,6,8,9,10</row>
          </intArray>
        </opTable>
      </op>
      <op>
        <opSymbol>
          <opName>e2</opName>
          <arity>1</arity>
        </opSymbol>
        <opTable>
          <intArray>
            <row>11,12,2,13,14,15,12,2,13,14,15,11,12,13,14,15</row>
          </intArray>
        </opTable>
      </op>
      <op>
        <opSymbol>
          <opName>s</opName>
          <arity>1</arity>
        </opSymbol>
        <opTable>
          <intArray>
            <row>0,1,2,3,4,5,0,0,0,0,0,2,2,2,2,2</row>
          </intArray>
        </opTable>
      </op>
      <op>
        <opSymbol>
          <opName>f</opName>
          <arity>1</arity>
        </opSymbol>
        <opTable>
          <intArray>
            <row>1,0,0,4,3,3,0,0,4,3,3,1,0,4,3,3</row>
          </intArray>
        </opTable>
      </op>
      <op>
        <opSymbol>
          <opName>g</opName>
          <arity>1</arity>
        </opSymbol>
        <opTable>
          <intArray>
            <row>4,5,5,1,2,2,5,5,1,2,2,4,5,1,2,2</row>
          </intArray>
        </opTable>
      </op>
      <op>
        <opSymbol>
          <opName>h</opName>
          <arity>1</arity>
        </opSymbol>
        <opTable>
          <intArray>
            <row>3,3,4,3,3,4,3,4,3,3,4,3,3,3,3,4</row>
          </intArray>
        </opTable>
      </op>
    </operations>
  </basicAlgebra>
</algebra>
</algebraList>
