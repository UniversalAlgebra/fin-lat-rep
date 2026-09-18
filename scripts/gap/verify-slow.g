# File: scripts/gap/verify-slow.g
#
# The article's slow group-theoretic computations, asserted.  Read by
# `make verify-slow`, which a scheduled CI job runs; not part of `make verify`,
# because Hexagon.g needs several gigabytes for the subgroup lattice of A11 and
# pentagonSearch.g takes six to thirteen minutes.  Run GAP with `-o 8g`.
#
# See verify-fast.g for the conventions; this file follows them.

dir := GAPInfo.SystemEnvironment.FINLATREPGAP_DIR;
failures := 0;

check := function(what, got, want)
    if got = want then
        Print("  ok    ", what, "\n");
    else
        Print("  FAIL  ", what, "\n        got  ", got, "\n        want ", want, "\n");
        failures := failures + 1;
    fi;
end;

Print("Hexagon.g: Palfy's example in A11\n");
Read(Concatenation(dir, "/Hexagon.g"));
check("H is C11 : C5",            StructureDescription(H), "C11 : C5");
check("[A11:H] = 9! = 362880",    Index(G, H), 362880);
check("M11 meets M11Other at H",  H = Intersection(M11, M11Other), true);
check("[H,A11] is the hexagon",   IntermediateSubgroups(G, H).inclusions,
                                  [[0,1],[0,2],[1,3],[2,4],[3,5],[4,5]]);

Print("pentagonSearch.g: SmallGroup(216,153) is the smallest with a pentagon upper interval\n");
Read(Concatenation(dir, "/pentagonSearch.g"));
found := pentagonSearch(3, 216);
check("exactly one group found",  Length(found), 1);
if Length(found) = 1 then
    check("it is SmallGroup(216,153)", [found[1].order, found[1].id], [216, 153]);
    check("twelve witnesses in one conjugacy class", [found[1].witnesses, found[1].classes], [12, 1]);
    check("each cyclic of order 6, index 36",
          [found[1].isomorphismType, found[1].subgroupOrders, found[1].indices], ["C6", [6], [36]]);
fi;

if failures > 0 then
    Print("\n", failures, " assertion(s) failed.\n");
    QUIT_GAP(1);
fi;
Print("\nAll slow GAP checks agree with the article.\n");
QUIT_GAP(0);
