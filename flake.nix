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

  outputs = { nixpkgs, github-project, ... }:
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
      mkUacalc = pkgs:
        let
          # Neither the jar nor its URL carries a version, so the version here
          # is the date the hashes below were measured.
          version = "unstable-2026-09-13";

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
              src = pkgs.fetchurl {
                url = "https://uacalc.org/uacalc.jar";
                hash = "sha256-zy4y+xGQnLBKSjWQrBtEj4kbMnrkqACh6q95aDKMTu4=";
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
        in
        {
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

            # One line, and on stderr, so that `nix develop --command ...`
            # leaves stdout to whatever it was asked to run.
            shellHook = ''
              echo "fin-lat-rep: gap, java, jython, uacalc, pdflatex, python3, make, gh${
                pkgs.lib.optionalString pkgs.stdenv.hostPlatform.isLinux ", xvfb-run"
              } on PATH" >&2
            '';
          };
        });
    };
}
