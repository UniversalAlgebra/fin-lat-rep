# Some GAP commands which show that lattice 17 is an interval 
# in the subgroup lattice of (A4 x A4) : C2 = SmallGroup(288,1025);

g:=SmallGroup(288,1025);;
cc:=ConjugacyClassesSubgroups(g);;
h:=Representative(cc[15]);;
inthg:=IntermediateSubgroups(g,h);

# This returns the covering relations
# [ [ 0, 1 ], [ 0, 2 ], [ 0, 3 ], [ 0, 4 ], [ 1, 6 ], [ 2, 5 ], [ 3, 5 ], [ 4, 5 ], [ 5, 6 ] ]
# so we see this is, indeed, lattice 17

# To draw the interval in XGAP,
l:=GraphicSubgroupLattice(g);;
InsertVertex(l,h);
for k in [1..Size(inthg.subgroups)] do
    InsertVertex(l,inthg.subgroups[k]);
od;
