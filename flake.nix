# File: flake.nix
#
# The development environment for this repository.  `nix develop` is meant to
# be the whole setup story: a shell holding the programs the article and its
# computations need, at the versions `flake.lock` pins, so that two people
# building the paper are running the same software.  What is here is GAP, a
# JDK, Jython, TeX Live, and the Universal Algebra Calculator, which the flake
# packages itself because it is in no package repository at all.
#
# The reason for pinning is recorded in docs/GITHUB_PROJECT.md: the article
# cites GAP 4.8.3 from 2016, and on a current GAP two of the programs that
# establish its group-theoretic claims had silently stopped establishing them,
# because they selected subgroups by position in a list whose order had
# changed.

{
  description = "Toolchain for the fin-lat-rep article and its computations";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-26.05";

  # The github-project roadmap engine, which keeps docs/GITHUB_PROJECT.md in
  # step with GitHub.  It is referenced, never vendored (issue #27): a copy of
  # its scripts in this repository is exactly the drift the plan exists to
  # stop.  `flake.lock` pins it, the apps below re-export it, the Makefile's
  # project-* targets call those, and `nix flake update github-project` is how
  # it moves.
  inputs.github-project.url = "github:williamdemeo/github-project";

  # The algebras themselves.  They live in UACalc/AlgebraFiles rather than in
  # this repository (see uacalc-files/README.md), and `make check-catalog`
  # needs them, so the shell hands them over rather than asking a contributor
  # to have a checkout in the right place.  Pinned, which the plan's M2-1
  # prefers over fetching at check time: a pinned copy is something the check
  # can be stale AGAINST, and `nix flake update algebrafiles` is how it moves.
  # Not a flake, so `flake = false` and the store path is the directory.
  inputs.algebrafiles = {
    url = "github:UACalc/AlgebraFiles";
    flake = false;
  };

  # The GAP programs behind the article's group-theoretic claims.  They moved
  # to their own repository in #23, and `make verify` re-runs the fast ones, so
  # the shell hands them over at a pinned revision for the same reason it hands
  # over the algebras: a floating clone would make the gate depend on
  # unreviewed upstream changes, which is the opposite of what a gate is for.
  # `nix flake update finlatrepgap` is how it moves.
  inputs.finlatrepgap = {
    url = "github:UniversalAlgebra/fin-lat-rep-gap";
    flake = false;
  };

  outputs = { nixpkgs, github-project, algebrafiles, finlatrepgap, ... }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      forAllSystems = f:
        nixpkgs.lib.genAttrs systems (system: f (import nixpkgs { inherit system; }));

      # The Universal Algebra Calculator.
      #
      # UACalc is in no package repository, so the flake assembles it out of
      # the artifacts its authors publish: a prebuilt `uacalc.jar` from the
      # project's web site, and the four supporting jars vendored in
      # UACalc/uacalcsrc.  Issue #26 records why the jar is taken rather than
      # built from source: that Ant build declares six dependency jars and
      # vendors four, targets Java 8, and carries Groovy 1.0 from 2007, and the
      # prebuilt jar is what uacalc.org serves everyone else anyway.
      #
      # THE FRAGILITY, WRITTEN DOWN.  `https://uacalc.org/uacalc.jar` carries
      # no version in its URL and is served from a personal web server, so the
      # bytes behind that name can change at any time and nothing about the
      # name would say so.  The sha256 below is a mitigation rather than a fix:
      # when the file changes, this build fails with a hash mismatch instead of
      # quietly handing everybody a different calculator.  What to do then is a
      # decision and not a chore.  Fetch the new jar, satisfy yourself that it
      # still computes what the article says it computes (`make uacalc-smoke`,
      # and the catalog check in docs/CHECKING-AN-ALGEBRA.md), then record the
      # new hash and date here and put the old hash in the commit message, so
      # the change is a fact in the history rather than a surprise.  The four
      # jars from uacalcsrc are pinned twice over, by commit and by content, so
      # they cannot move at all.
      #
      # Two commands reach the devShell's PATH from this, as follows:
      #
      #   uacalc      the Swing GUI, `org.uacalc.nbui.UACalculator2`, which is
      #               the jar's only Main-Class.
      #   uacalc-cli  Jython with the same five jars importable, which is how
      #               UACalc is driven without a display.  Given a script it
      #               runs it; given nothing it is the interactive command line
      #               documented at uacalc-at-the-command-line.
      # Neither the jar nor its URL carries a version, so the version here is
      # the date the hashes were measured.  Out here rather than inside
      # mkUacalc because the devShell's banner names it too.
      uacalcVersion = "unstable-2026-09-13";

      mkUacalc = pkgs:
        let
          version = uacalcVersion;

          uacalcsrcRev = "538ec6a0adaaee2c81ff1a481238d944d63ce4c7";

          # One fetchurl per jar at that commit downloads 2.5 MB rather than
          # the whole repository, and pins each jar by content as well.
          fromUacalcsrc = name: hash: pkgs.fetchurl {
            url = "https://raw.githubusercontent.com/UACalc/uacalcsrc/${uacalcsrcRev}/jars/${name}";
            inherit hash;
          };

          # List rather than attribute set, because the order is the classpath
          # order.  The manifest's Class-Path entry also names
          # designgridlayout-1.1p1.jar and swing-layout-1.0.2.jar, which exist
          # in neither repository and are not needed: designgridlayout is
          # imported only by UACalculatorUI.java, which the UACalculator2 entry
          # point does not reach.
          jars = [
            {
              name = "uacalc.jar";
              # Two sources for the same bytes.  uacalc.org is the origin, and
              # GitHub's runners could not connect to it in two of the first
              # five CI fetches (issue #39; nine minutes of connection
              # timeouts each).  The Internet Archive's capture of 2024-06-13
              # is byte-identical to what uacalc.org serves today (measured:
              # same sha256, 998189 bytes), and its `id_` URL serves the
              # original file rather than a rewritten page, so it stands in
              # under the same hash.  fetchurl tries the URLs in order, each
              # with curl's own retries; the connect timeout is what makes a
              # dead first host cost about a minute rather than nine.
              src = pkgs.fetchurl {
                urls = [
                  "https://uacalc.org/uacalc.jar"
                  "https://web.archive.org/web/20240613221112id_/https://uacalc.org/uacalc.jar"
                ];
                hash = "sha256-zy4y+xGQnLBKSjWQrBtEj4kbMnrkqACh6q95aDKMTu4=";
                curlOptsList = [ "--connect-timeout" "20" ];
              };
            }
            {
              name = "LatDraw.jar";
              src = fromUacalcsrc "LatDraw.jar"
                "sha256-Q86wG7nEDE5tvTN+WFHxDrvq0aKt5uWYlGz2MJoXqhw=";
            }
            {
              name = "miglayout-3.7-swing.jar";
              src = fromUacalcsrc "miglayout-3.7-swing.jar"
                "sha256-2cq2nZwm9L/AzCGE3cSBSmDGVC58/UTcLUJzDzn93ko=";
            }
            {
              name = "groovy-all-1.0.jar";
              src = fromUacalcsrc "groovy-all-1.0.jar"
                "sha256-vtsJrABQ3aOSBJxm5K2SkYBQ3iLEQxfjxDvz700XyQc=";
            }
            {
              name = "groovy-engine.jar";
              src = fromUacalcsrc "groovy-engine.jar"
                "sha256-TEEpGMo5jR2gLviwnasFClirKzch7CPwi+uRtvxAd6M=";
            }
          ];

          inherit (pkgs.lib) concatMapStringsSep;
        in
        pkgs.runCommand "uacalc-${version}"
          {
            nativeBuildInputs = [ pkgs.makeWrapper ];
            meta = {
              description =
                "Universal Algebra Calculator: the GUI and its Jython command line";
              homepage = "https://uacalc.org";
              mainProgram = "uacalc";
              platforms = pkgs.lib.platforms.unix;
            };
          }
          ''
            mkdir -p $out/share/uacalc $out/bin
            ${concatMapStringsSep "\n            "
                (j: "install -m444 ${j.src} $out/share/uacalc/${j.name}") jars}

            jars="${concatMapStringsSep ":" (j: "$out/share/uacalc/${j.name}") jars}"

            makeWrapper ${pkgs.jdk21}/bin/java $out/bin/uacalc \
              --add-flags "-cp $jars org.uacalc.nbui.UACalculator2"

            # JYTHONPATH, not CLASSPATH, is what puts these jars on Jython's
            # sys.path.  nixpkgs runs Jython as `java -jar jython.jar`, and
            # `java -jar` ignores both -cp and CLASSPATH, so a CLASSPATH on its
            # own gives "ImportError: No module named uacalc" (measured).
            # CLASSPATH is set regardless, for any JVM a session starts for
            # itself, and UACALC_JARS is the variable the scripts under
            # scripts/jython/ read to put the same five jars on sys.path
            # without having to know where they came from.
            makeWrapper ${pkgs.jython}/bin/jython $out/bin/uacalc-cli \
              --set JYTHONPATH "$jars" \
              --set CLASSPATH "$jars" \
              --set UACALC_JARS "$jars"
          '';
    in
    {
      # `nix build .#uacalc` builds the calculator on its own, which is what
      # CI and anyone diagnosing a hash mismatch wants; the devShell below
      # puts the same derivation on PATH.
      packages = forAllSystems (pkgs: { uacalc = mkUacalc pkgs; });

      # The roadmap engine's apps, re-exported under a ghproject- prefix, so
      # that `nix run .#ghproject-update -- docs/GITHUB_PROJECT.md` runs the
      # engine at the version THIS repository's flake.lock pins rather than
      # whatever is on the machine.  The Makefile's project-* targets call
      # these.
      apps = nixpkgs.lib.genAttrs systems (system:
        nixpkgs.lib.mapAttrs'
          (name: app: nixpkgs.lib.nameValuePair "ghproject-${name}" app)
          github-project.apps.${system});

      checks = forAllSystems (pkgs:
        # X is a Linux concern here, so the smoke test is too; on Darwin the
        # flake has no checks.
        nixpkgs.lib.optionalAttrs pkgs.stdenv.hostPlatform.isLinux {
          # Milestone 1's exit criterion for UACalc, as `nix flake check` as
          # well as `make uacalc-smoke`.  A GUI does not exit, so the test is
          # that it is still alive when a timeout fires, which `timeout`
          # reports as status 124.
          #
          # What that does and does not establish, measured rather than
          # assumed.  Given no framebuffer the same command exits 0, after
          # printing a HeadlessException; given an unreadable uacalc.jar it
          # exits 1.  So a 124 really does say that the application started
          # and put a window up, and a JDK bump that broke Swing would be
          # caught here.  It says nothing about the four supporting jars,
          # which are loaded lazily, when a lattice is drawn: the GUI comes up
          # just as silently without them.  What guards those is the content
          # hash on each one, not this test.
          uacalc-smoke = pkgs.runCommand "uacalc-smoke"
            {
              nativeBuildInputs = [ pkgs.coreutils pkgs.xvfb-run (mkUacalc pkgs) ];
            }
            ''
              # Swing wants somewhere to put its preferences; the sandbox has
              # no home directory.
              export HOME="$TMPDIR"

              status=0
              timeout 30 xvfb-run -a uacalc || status=$?
              test "$status" -eq 124 || {
                echo "uacalc exited with status $status; expected 124," >&2
                echo "which is the timeout firing on a window still up." >&2
                exit 1
              }
              touch "$out"
            '';
        });

      devShells = forAllSystems (pkgs:
        let
          # TeX Live, restricted to what article/Makefile actually needs.
          #
          # `.github/workflows/build-paper.yml` installs the Debian collections
          # texlive-latex-extra, texlive-fonts-extra, texlive-science,
          # texlive-pictures, texlive-bibtex-extra and texlive-plain-generic.
          # Their nixpkgs equivalents come to a 3794 MiB closure against
          # this list's 441 MiB, measured with `nix path-info -S
          # --closure-size`, which is the several gigabytes issue #25 asks us
          # to avoid.  So the list is by name rather than by collection.
          # Every entry was arrived at by building the article and reading
          # what pdflatex could not find, so each one is load-bearing unless
          # its comment says otherwise.
          #
          # To add a package, name the file's owner rather than guessing: TeX
          # Live's own database knows, and this prints it.
          #
          #   xz -dc "$(nix build --no-link --print-out-paths \
          #             nixpkgs#texlive.tlpdb.xz)" \
          #     | awk '/^name /{p=$2} /\/scalefnt\.sty$/{print p}'
          #   carlisle
          texlive-article = pkgs.texlive.withPackages (ps: with ps; [
            scheme-basic # pdftex, bibtex, kpathsea, the LaTeX kernel, Computer Modern
            amsmath      # amsmath, amscd, and the amstex.sty au.cls loads
            amsfonts     # amssymb, euscript, and the msam/msbm fonts
            amscls       # amsthm and amsart.cls; also the upref named below
            graphics     # color, graphicx
            tools        # enumerate, xspace, showkeys
            url
            jknapltx     # mathrsfs
            comment
            stmaryrd
            carlisle     # scalefnt; there is no package called scalefnt
            pgf          # tikz, and the calc library the diagrams use
            hyperref
            acronym
            rsfs         # rsfs10, the script font mathrsfs selects
            helvetic     # phvb, the Helvetica Bold au.cls sets its logo in
            bibtex       # plain.bst, for \bibliographystyle{plain}

            # acronym requires these three, and TeX Live does not record the
            # dependency, so withPackages cannot pull them in on its own.
            # suffix.sty is in bigfoot; relsize arrives with the `smaller`
            # option, which the article passes.
            bigfoot
            xstring
            relsize

            # au.cls loads crop and upref in its `crop` branch and geometry in
            # its `geom` branch.  The article enables neither option today, so
            # the current build reaches neither; they are here so that turning
            # an option on is not a missing-file error.
            crop
            geometry
          ]);

          # texlive.withPackages yields a derivation named
          # texlive-<year>-r<rev>-final-env and carries no .version, so the
          # banner takes the year and revision out of that name.  Both removals
          # are no-ops if nixpkgs ever changes the shape, which leaves the
          # banner showing the raw name rather than failing to evaluate.
          texliveVersion = with pkgs.lib;
            removeSuffix "-final-env" (removePrefix "texlive-" texlive-article.name);

          # One more row for the banner's printf, on the platforms that have
          # xvfb-run.  Built here rather than inside the shellHook, because a
          # nested indented string inside an interpolation does not parse.
          xvfbRow =
            if pkgs.stdenv.hostPlatform.isLinux
            then " \\\n    xvfb-run   '${pkgs.xvfb-run.version}' 'X virtual framebuffer'"
            else "";
        in
        rec {
          default = pkgs.mkShellNoCC {
            name = "fin-lat-rep";

            packages = [
              # GAP, for the programs in UniversalAlgebra/fin-lat-rep-gap.  The
              # Small Groups Library is part of the nixpkgs build, so no
              # separate package is needed.
              pkgs.gap

              # A JDK, for the Universal Algebra Calculator.  Issue #26 records
              # the measurements: UACalc's jar is Java 8 bytecode but OpenJDK
              # 21 runs it, so there is no need to pin Java 8.  Named jdk21
              # rather than jdk so that a later `nix flake update` cannot move
              # UACalc onto a JDK nobody has tried it on.
              pkgs.jdk21

              # Jython is how UACalc is driven without a display.  Prefer it to
              # the jython-standalone-2.7-b1.jar vendored in UACalc/UACalc_CLI,
              # which is a 2014 beta in a repository carrying no license.
              pkgs.jython

              # The calculator itself: `uacalc` for the GUI, `uacalc-cli` for
              # the Jython command line, both with the five jars already on
              # the classpath.  Packaged at the top of this file.
              (mkUacalc pkgs)

              texlive-article

              pkgs.python3
              pkgs.gnumake

              # The github-project engine shells out to gh, and issue #27's
              # GHPROJECT_DIR escape hatch runs its scripts directly rather
              # than through the engine's own wrapper, so gh has to be here or
              # `make project-populate` cannot work from a fresh nix develop.
              pkgs.gh
            ]
            # xvfb-run, for the headless UACalc GUI smoke test of issue #26.  X
            # is a Linux concern here; on Darwin the shell does without it.
            ++ pkgs.lib.optional pkgs.stdenv.hostPlatform.isLinux pkgs.xvfb-run;

            # `make check-catalog` reads $(ALGEBRAFILES_DIR), whose default in
            # the Makefile is a personal checkout path; `?=` yields to this, so
            # inside the shell the check runs against the pinned algebras with
            # no argument and no checkout, and outside it the Makefile default
            # still applies.
            ALGEBRAFILES_DIR = "${algebrafiles}";

            # Likewise for the GAP programs; `make verify-gap` reads this.
            FINLATREPGAP_DIR = "${finlatrepgap}";

            # The greeting.
            #
            # All of it goes to stderr, so that `nix develop --command ...`
            # leaves stdout to whatever it was asked to run, and it prints only
            # for an interactive shell, because issue #25 asked that the hook
            # not put a banner in front of every invocation and a `make paper`
            # in CI should stay quiet.  `case $- in *i*)` is that test.
            #
            # It is a function, and exported, so that somebody who has scrolled
            # past it can type `finlatrep-tools` to see it again, and so that
            # the rendering can be checked from a non-interactive shell.
            #
            # The versions are read from the pinned nixpkgs when the flake is
            # evaluated, not by running each program when the shell opens: the
            # banner therefore costs nothing to print, and it reports what
            # flake.lock pins rather than whatever answers first on PATH.  Keep
            # the command list in step with the Makefile's own `## ` help text.
            shellHook = ''
              finlatrep-tools () {
                {
                  echo "✅ fin-lat-rep dev shell"
                  echo " The following tools are provided (versions pinned by flake.lock):"
                  printf '  %-11s %-19s %s\n' \
                     gap        '${pkgs.gap.version}'     'GAP, with the Small Groups Library' \
                     java       '${pkgs.jdk21.version}'   'OpenJDK' \
                     jython     '${pkgs.jython.version}'  'Jython, which is Python 2 on the JVM' \
                     uacalc     '${uacalcVersion}'        'Universal Algebra Calculator, the GUI' \
                     uacalc-cli '${uacalcVersion}'        'the calculator, driven from Jython' \
                     pdflatex   '${texliveVersion}'       'TeX Live' \
                     python3    '${pkgs.python3.version}' 'Python' \
                     make       '${pkgs.gnumake.version}' 'GNU Make' \
                     gh         '${pkgs.gh.version}'      'GitHub CLI'${xvfbRow}
                  echo
                  echo '  The algebras are pinned too: $ALGEBRAFILES_DIR holds the .ua files,'
                  echo '  and $FINLATREPGAP_DIR holds the GAP programs.  `make verify` runs both.'
                  echo
                  echo ' ----------------------------------------------'
                  echo '  # some commands you can run in this shell:'
                  echo '  make paper          # build article/SmallLatticeReps.pdf'
                  echo '  make check-catalog  # check every algebra against the lattice drawn beside it'
                  echo '  make uacalc-smoke   # check that the calculator comes up (Linux only)'
                  echo '  make verify         # the computational checks CI runs on a pull request'
                  echo '  make help           # list every target'
                  echo ' ----------------------------------------------'
                  echo
                } >&2
              }
              export -f finlatrep-tools
              case $- in *i*) finlatrep-tools ;; esac
            '';
          };

          # The same shell without TeX Live, for the verification workflows
          # (`nix develop .#ci`).  Issue #30's `make verify` builds no PDF, and
          # texlive-article is the largest closure in the shell by far, so CI
          # has no reason to fetch it; the paper's own workflow does.  Derived
          # from `default` rather than written out twice, so the two cannot
          # drift (the `rec` above is what lets it name `default`):
          # mkShellNoCC puts `packages` into nativeBuildInputs, and this
          # removes the one entry.  The banner still names pdflatex, but
          # it prints only in an interactive shell, which this is not.
          ci = default.overrideAttrs (old: {
            name = "fin-lat-rep-ci";
            nativeBuildInputs =
              pkgs.lib.filter (p: p != texlive-article) old.nativeBuildInputs;
          });
        });
    };
}
