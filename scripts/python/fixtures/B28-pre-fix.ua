<?xml version="1.0"?>
<!-- The B28 that stood in UACalc/AlgebraFiles from 2017-08-02 until
     2026-09-13, at commit 9e1ef390ef7a1288cdabdfb449d23c9095c02173.
     It has six operations rather than seven and its congruence lattice has
     eight elements, so it is NOT L28.  Kept as a regression fixture: the
     catalog check must fail on this file.  See fin-lat-rep issues #20, #22. -->
<algebraList>
<algebra>
  <basicAlgebra>
    <algName>B28</algName>
    <cardinality>16</cardinality>
    <operations>
      <op>
        <opSymbol>
          <opName>h2</opName>
          <arity>1</arity>
        </opSymbol>
        <opTable>
          <intArray>
            <row>0, 1, 2, 3, 4, 5, 0, 0, 0, 0, 0, 2, 2, 2, 2, 2</row>
          </intArray>
        </opTable>
      </op>
      <op>
        <opSymbol>
          <opName>h3</opName>
          <arity>1</arity>
        </opSymbol>
        <opTable>
          <intArray>
            <row>3, 3, 4, 3, 3, 4, 3, 4, 3, 3, 4, 3, 3, 3, 3, 4</row>
          </intArray>
        </opTable>
      </op>
      <op>
        <opSymbol>
          <opName>h0</opName>
          <arity>1</arity>
        </opSymbol>
        <opTable>
          <intArray>
            <row>0, 6, 7, 8, 9, 10, 6, 7, 8, 9, 10, 0, 6, 8, 9, 10</row>
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
            <row>11, 12, 2, 13, 14, 15, 12, 2, 13, 14, 15, 11, 12, 13, 14, 15</row>
          </intArray>
        </opTable>
      </op>
      <op>
        <opSymbol>
          <opName>h4</opName>
          <arity>1</arity>
        </opSymbol>
        <opTable>
          <intArray>
            <row>1, 0, 0, 4, 3, 3, 0, 0, 4, 3, 3, 1, 0, 4, 3, 3</row>
          </intArray>
        </opTable>
      </op>
      <op>
        <opSymbol>
          <opName>h5</opName>
          <arity>1</arity>
        </opSymbol>
        <opTable>
          <intArray>
            <row>4, 5, 5, 1, 2, 2, 5, 5, 1, 2, 2, 4, 5, 1, 2, 2</row>
          </intArray>
        </opTable>
      </op>
    </operations>
  </basicAlgebra>
</algebra>
</algebraList>
