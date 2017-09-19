InstallMethod(IntermediateSubgroups,"using maximal subgroups",
  IsIdenticalObj, [IsGroup,IsGroup],
  1, # better than previous if index larger
function(G,U)
local uind,subs,incl,i,j,k,m,gens,t,c,p;
  if (not IsFinite(G)) and Index(G,U)=infinity then
    TryNextMethod();
  fi;
  uind:=IndexNC(G,U);
  if uind<200 then
    TryNextMethod();
  fi;
  subs:=[G]; #subgroups so far
  incl:=[];
  i:=1;
  gens:=SmallGeneratingSet(U);
  while i<=Length(subs) do
    # find all maximals containing U
    m:=MaximalSubgroupClassReps(subs[i]);
    m:=Filtered(m,x->IndexNC(subs[i],U) mod IndexNC(subs[i],x)=0);
    Info(InfoLattice,1,"Subgroup ",i,", Order ",Size(subs[i]),": ",Length(m),
      " maxes");
    for j in m do
      t:=RightTransversal(subs[i],Normalizer(subs[i],j)); # conjugates
      for k in t do
        if ForAll(gens,x->k*x/k in j) then
          # U is contained in j^k
          c:=j^k;
          Assert(1,IsSubset(c,U));
          #is it U?
          if uind=IndexNC(G,c) then
            Add(incl,[0,i]);
          else
            # is it new?
            p:=PositionProperty(subs,x->IndexNC(G,x)=IndexNC(G,c) and
              ForAll(GeneratorsOfGroup(c),y->y in x));
            if p<>fail then
              Add(incl,[p,i]);
            else
              Add(subs,c);
              Add(incl,[Length(subs),i]);
            fi;
          fi;
        fi;
      od;
    od;
    i:=i+1;
  od;
  # rearrange
  c:=List(subs,x->IndexNC(x,U));
  p:=Sortex(c);
  subs:=Permuted(subs,p);
  subs:=subs{[1..Length(subs)-1]}; # remove whole group
  for i in incl do
    if i[1]>0 then i[1]:=i[1]^p; fi;
    if i[2]>0 then i[2]:=i[2]^p; fi;
  od;
  Sort(incl);
  return rec(inclusions:=incl,subgroups:=subs);
end);
