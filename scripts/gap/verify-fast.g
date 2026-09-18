# File: scripts/gap/verify-fast.g
#
# Re-run the article's fast group-theoretic computations and assert that they
# still say what the article says.  Read by `make verify-gap`, which is part of
# `make verify`.  Exits 0 when every assertion holds and 1 otherwise, so that
# CI can gate on it; GAP's QUIT_GAP sets the process exit status.
#
# What runs here is chosen by time: PJ17.gap takes seconds and PJ11.gap under
# a minute.  Hexagon.g and pentagonSearch.g take minutes and gigabytes and are
# in verify-slow.g, which a scheduled job runs instead.
#
# The programs come from UniversalAlgebra/fin-lat-rep-gap at the revision
# flake.lock pins; the dev shell exports FINLATREPGAP_DIR.  They are read, not
# copied, so the assertion below is against the same file the article cites.
#
# The expected values are the ones the article states, in Section 3 for L11
# and in Section 4.1 for L17.  If one of these assertions fails after a GAP
# upgrade, the likeliest cause is the index drift recorded in Remark 3.7: a
# subgroup selected by position in a list whose order changed.

# GAP wraps its output at the screen width, 80 columns when there is no
# terminal, which broke the marked lines below in two; 4096 is the widest
# it allows.
SizeScreen([ 4096 ]);

# Fail closed.  Until QUIT_GAP(0) at the very end says otherwise, this run
# has failed: if a Read below stops parsing, or an error breaks the flow so
# that the end is never reached, GAP exits with this status rather than 0.
# The Makefile adds --quitonbreak and stdin from /dev/null, so an error
# cannot wait in the break loop either (measured: a syntax error in this
# file once held `make verify` for eleven minutes, waiting on stdin).
GAP_EXIT_CODE(1);

dir := GAPInfo.SystemEnvironment.FINLATREPGAP_DIR;
me := "verify-fast.g";
passes := 0;
failures := 0;

check := function(what, got, want)
    if got = want then
        Print("✅ ", me, "  ", what, "\n");
        passes := passes + 1;
    else
        Print("❌ ", me, "  ", what, "\n        got  ", got, "\n        want ", want, "\n");
        failures := failures + 1;
    fi;
end;

Print("PJ17.gap: L17 as an interval in SmallGroup(288,1025)\n");
Read(Concatenation(dir, "/PJ17.gap"));
check("|G| = 288",                Size(g), 288);
check("[G:H] = 48",               Index(g, h), 48);
check("covers of [H,G] are L17's",
      inthg.inclusions, [[0,1],[0,2],[0,3],[0,4],[1,6],[2,5],[3,5],[4,5],[5,6]]);

Print("PJ11.gap: L11 as filter-ideal in SmallGroup(216,153)\n");
Read(Concatenation(dir, "/PJ11.gap"));
check("[H,G] is the pentagon",    intHG.inclusions, [[0,1],[0,2],[1,3],[2,4],[3,4]]);
check("[G:H] = 36",               Index(G, H), 36);
check("K below B only",           [IsSubgroup(A,K), IsSubgroup(B,K), IsSubgroup(C,K)], [false, true, false]);
check("H is C6",                  StructureDescription(H), "C6");
check("[G:M1] = 108",             Index(G, M1), 108);
check("[G:M2] = 72",              Index(G, M2), 72);
check("a cover of M1 in B avoids A and C",
      ForAny([1..Length(intM1B.subgroups)],
             i -> [0,i] in intM1B.inclusions
                  and not IsSubgroup(A, intM1B.subgroups[i])
                  and not IsSubgroup(C, intM1B.subgroups[i])), true);
check("no cover of M2 in B avoids both A and C, so 108 is the best this gives",
      ForAny([1..Length(intM2B.subgroups)],
             i -> [0,i] in intM2B.inclusions
                  and not IsSubgroup(A, intM2B.subgroups[i])
                  and not IsSubgroup(C, intM2B.subgroups[i])), false);

if failures > 0 then
    Print("\n❌ ", me, "  ", failures, " of ", passes + failures, " assertions failed.\n");
    QUIT_GAP(1);
fi;
Print("\n✅ ", me, "  all ", passes, " assertions hold; the fast GAP checks agree with the article.\n");
QUIT_GAP(0);
