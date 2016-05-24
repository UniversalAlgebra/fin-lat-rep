# GAP code to Check that Palfy's example in [1] p. 477 is a hexagon.
#
# [1] Palfy, "On Feit's Examples of Intervals in Subgroup Lattices" J. Algebra, 116 (1988).
#
# williamdemeo@gmail.com
# 2012.10.27

G:=AlternatingGroup(11);
ccms:=ConjugacyClassesMaximalSubgroups(G);;  # there are 7

# The members of the 6th and 7th conjugacy class of maximal subgroups are isomorphic to M11
M11:=Representative(ccms[6]);
mscr:=MaximalSubgroupClassReps(M11);
K1:=mscr[4];  # PSL(2,11)
mscr:=MaximalSubgroupClassReps(K1);
H:=mscr[2];   # C11 : C5

# Now find another M11 maximal subgroup of G that contains H.

# There are only two maximal subgroups of G containing H.
# Proof:
count:=0;
for MC in ccms do
    for M in MC do
        if IsSubgroup(M,H) then
            count:=count+1;
        fi;
    od;
od;
Print("There are ", count, " maximal subgroups of A11 containing H.\n");

# The other maximal subgroup containing H is an M11 in the 
# 7th conjugacy class of maximal subgroups. 
for M in ccms[7] do
    if IsSubgroup(M,H) then
        M11Other:=M;
    fi;
od;

# Check that M11 and M11Other meet at H:
H = Intersection(M11,M11Other);  # returns true

# Check that the intervals [H,M11] and [H,M11Other] are 3 element chains:
IntermediateSubgroups(M11,H);
IntermediateSubgroups(M11Other,H);



  

