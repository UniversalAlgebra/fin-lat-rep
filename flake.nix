# File: flake.nix
#
# The development environment for this repository.  `nix develop` is meant to
# be the whole setup story: a shell holding the programs the article and its
# computations need, at the versions `flake.lock` pins, so that two people
# building the paper are running the same software.  The Universal Algebra
# Calculator itself is added by issue #26; what is here is the JDK and the
# Jython it runs on.
#
# The reason for pinning is recorded in docs/GITHUB_PROJECT.md: the article
# cites GAP 4.8.3 from 2016, and on a current GAP two of the programs that
# establish its group-theoretic claims had silently stopped establishing them,
# because they selected subgroups by position in a list whose order had
# changed.

{
  description = "Toolchain for the fin-lat-rep article and its computations";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-26.05";

  outputs = { nixpkgs, ... }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      forAllSystems = f:
        nixpkgs.lib.genAttrs systems (system: f (import nixpkgs { inherit system; }));
    in
    {
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
              echo "fin-lat-rep: gap, java, jython, pdflatex, python3, make, gh${
                pkgs.lib.optionalString pkgs.stdenv.hostPlatform.isLinux ", xvfb-run"
              } on PATH" >&2
            '';
          };
        });
    };
}
