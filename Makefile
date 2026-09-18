# File: Makefile
#
# Front door for the repository.  It carries the paper, the catalog check from
# issue #29, the Universal Algebra Calculator's smoke test from issue #26, the
# project targets from issue #27, which drive the github-project engine, and
# `verify`, from issue #30: every computational check that gates a change.
# CI runs `verify` and, beside it, `nix flake check`; see the note at `verify`.
#
# Every target expects the development shell.  Run `nix develop` first: that
# is where pdflatex, uacalc and xvfb-run are, and nothing here asks you to
# install them yourself.  See CONTRIBUTING.md.

PYTHON ?= python3
PYTHON_DIR := scripts/python
ARTICLE := article/SmallLatticeReps.tex

# The algebras live in UACalc/AlgebraFiles, not here; see uacalc-files/README.md.
# Inside `nix develop` the shell sets ALGEBRAFILES_DIR to the pinned flake
# input and `?=` yields to it, so the check runs against the same algebras in
# CI and on every machine.  The default below is for a shell without Nix; point
# it at a checkout, or set ALGEBRA_FILE to any .ua file you want checked.
ALGEBRAFILES_DIR ?= $(HOME)/git/UACalc/AlgebraFiles/master
ALGEBRA_FILE ?= $(ALGEBRAFILES_DIR)/CongruenceLatReps/SmallLatticeReps.ua

# The GAP programs live in UniversalAlgebra/fin-lat-rep-gap, pinned the same
# way; `make verify-gap` reads them from here.  See programs/README.md.
FINLATREPGAP_DIR ?= $(HOME)/git/UniversalAlgebra/fin-lat-rep-gap/main

# Where `make verify` writes the UACalc table it then checks against.
BUILD := build

# Cross-check against UACalc itself.  Optional: unset, the check runs on its
# own implementation alone.  See docs/CHECKING-AN-ALGEBRA.md.
UACALC_TABLE ?=
ifneq (,$(UACALC_TABLE))
# abspath, because the recipe cd's into scripts/python before this is used.
CHECK_FLAGS := --uacalc-table $(abspath $(UACALC_TABLE))
else
CHECK_FLAGS :=
endif

PLAN := docs/GITHUB_PROJECT.md

# The github-project engine, which keeps $(PLAN) and GitHub in step, is
# referenced and never vendored: it arrives as a flake input, pinned in
# flake.lock, and these targets run it through the ghproject-* apps that
# flake.nix re-exports.  Upgrade it deliberately, with
# `nix flake update github-project`.  project-lint is offline; the others talk
# to GitHub through an authenticated `gh`.
#
# Escape hatch, for working on the engine itself or on a machine without Nix:
# set GHPROJECT_DIR to a github-project checkout and the targets call its
# scripts with plain python3, which is all the engine needs.
GHPROJECT_DIR ?=

ifneq (,$(GHPROJECT_DIR))
GHPROJECT_LINT         := $(PYTHON) "$(GHPROJECT_DIR)/scripts/gh_project_lint.py"
GHPROJECT_POPULATE     := $(PYTHON) "$(GHPROJECT_DIR)/scripts/gh_project_populate.py"
GHPROJECT_UPDATE       := $(PYTHON) "$(GHPROJECT_DIR)/scripts/gh_project_update.py"
GHPROJECT_UPDATE_CHECK := $(PYTHON) "$(GHPROJECT_DIR)/scripts/gh_project_update.py" --check
else
# The backslash is not optional: an unescaped # starts a comment even inside
# a make assignment, so `nix run .#ghproject-lint` would assign `nix run .`.
GHPROJECT_LINT         := nix run .\#ghproject-lint --
GHPROJECT_POPULATE     := nix run .\#ghproject-populate --
GHPROJECT_UPDATE       := nix run .\#ghproject-update --
GHPROJECT_UPDATE_CHECK := nix run .\#ghproject-update-check --
endif

.PHONY: help paper check-catalog uacalc-smoke uacalc-table verify verify-gap \
        verify-slow test test-finlatrep test-utils clean \
        project-lint project-populate-dry project-populate \
        project-update project-update-check _check-ghproject

# The column is 20 rather than 16, because project-update-check and
# project-populate-dry are twenty characters and ran into their descriptions.
help: ## Show this help
	@grep -hE '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) \
	  | awk -F':.*?## ' '{printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

paper: ## Build article/SmallLatticeReps.pdf
	$(MAKE) -C article

check-catalog: ## Check every algebra against the lattice the article draws
	@test -f "$(ALGEBRA_FILE)" || { \
	  echo "error: no algebra file at $(ALGEBRA_FILE)"; \
	  echo "       clone UACalc/AlgebraFiles and set ALGEBRAFILES_DIR, or set"; \
	  echo "       ALGEBRA_FILE directly.  See docs/CHECKING-AN-ALGEBRA.md."; \
	  exit 2; }
	cd $(PYTHON_DIR) && PYTHONPATH=. $(PYTHON) -m finlatrep.check $(CHECK_FLAGS) \
	  "$(abspath $(ALGEBRA_FILE))" "$(abspath $(ARTICLE))"

# Milestone 1's exit criterion for UACalc.  A GUI does not exit, so the test
# is that it is still alive when the timeout fires, which `timeout` reports as
# status 124; given no display it exits 0 instead, and given no uacalc.jar it
# exits 1.  `nix flake check` runs the same test in the sandbox.
#
# Linux only, because xvfb-run is: flake.nix puts it in the shell on Linux and
# not on Darwin.  The guard says that, rather than leaving a Darwin reader with
# `xvfb-run: command not found` to interpret.
uacalc-smoke: ## Check the UACalc GUI comes up and stays up (Linux only)
	@command -v xvfb-run > /dev/null || { \
	  echo "error: xvfb-run is not on PATH, so this target cannot run here."; \
	  echo "       It is Linux only; the dev shell omits xvfb-run on Darwin."; \
	  echo "       Run 'uacalc' yourself to see the GUI."; \
	  exit 2; }
	timeout 30 xvfb-run -a uacalc; test $$? -eq 124

# The second engine: UACalc itself, driven through its Jython command line,
# writing the `<name> <card> <con>` table that check-catalog compares against.
# `uacalc-cli` is the dev shell's wrapper with the five jars on the classpath.
uacalc-table: ## Compute |Con(A)| for every algebra with UACalc itself
	@command -v uacalc-cli > /dev/null || { \
	  echo "error: uacalc-cli is not on PATH; run this inside 'nix develop'."; \
	  exit 2; }
	@test -f "$(ALGEBRA_FILE)" || { echo "error: no algebra file at $(ALGEBRA_FILE)"; exit 2; }
	@mkdir -p $(BUILD)
	@uacalc-cli scripts/jython/con_table.py "$(ALGEBRA_FILE)" > $(BUILD)/uacalc-table.txt \
	  || { echo "❌ scripts/jython/con_table.py  UACalc could not compute the table"; exit 1; }
	@echo "✅ scripts/jython/con_table.py  UACalc computed |A| and |Con(A)| for $$(wc -l < $(BUILD)/uacalc-table.txt) algebras, in $(BUILD)/uacalc-table.txt"

# The fast group-theoretic checks: PJ17.gap in seconds, PJ11.gap in under a
# minute.  scripts/gap/verify-fast.g reads them from the pinned programs and
# asserts what the article says; GAP exits 1 on any failed assertion.#
# Three things make the GAP steps fail closed rather than hang or pass by
# accident: the driver's first statement is GAP_EXIT_CODE(1), so a run that
# never reaches its final QUIT_GAP(0) exits 1; --quitonbreak turns any error
# into exit 1 instead of a break loop; and stdin comes from /dev/null, so
# nothing can wait for a keyboard (a broken driver once held `make verify`
# for eleven minutes at GAP's break prompt, and CI would have waited for its
# timeout).

verify-gap: ## Re-run the fast GAP computations and assert the article's numbers
	@command -v gap > /dev/null || { \
	  echo "error: gap is not on PATH; run this inside 'nix develop'."; exit 2; }
	@test -f "$(FINLATREPGAP_DIR)/PJ11.gap" || { \
	  echo "error: no GAP programs at $(FINLATREPGAP_DIR)"; \
	  echo "       inside 'nix develop' this is set for you; outside it, clone"; \
	  echo "       UniversalAlgebra/fin-lat-rep-gap and set FINLATREPGAP_DIR."; \
	  exit 2; }
	FINLATREPGAP_DIR="$(abspath $(FINLATREPGAP_DIR))" gap -q -b -A --quitonbreak -o 4g scripts/gap/verify-fast.g < /dev/null

# Every computational check that gates a change, in the order that fails
# fastest: the unit suites, then the catalog check with UACalc as the second
# engine, then GAP.  Sub-makes rather than prerequisites so the order holds
# under -j too.
#
# CI runs this and `nix flake check`, which evaluates every flake output and
# runs the UACalc smoke test.  That one is not folded in here because every
# target in this file runs without Nix, and the two answer different
# questions: `verify` asks whether the mathematics still holds, `nix flake
# check` whether the environment still builds.  Run it yourself after
# touching flake.nix or flake.lock.
verify: ## Run the computational checks that gate a change (CI runs this and nix flake check)
	@echo "== make test: the unit suites, one line per test =="
	@$(MAKE) --no-print-directory test
	@echo
	@echo "== make uacalc-table: UACalc computes every algebra's congruence lattice =="
	@$(MAKE) --no-print-directory uacalc-table
	@echo
	@echo "== make check-catalog: our reading against the article's diagrams, and against UACalc =="
	@$(MAKE) --no-print-directory check-catalog UACALC_TABLE=$(BUILD)/uacalc-table.txt
	@echo
	@echo "== make verify-gap: the fast GAP computations against the article's numbers =="
	@$(MAKE) --no-print-directory verify-gap
	@echo
	@echo "✅ make verify  every stage passed"

# The slow half: Hexagon.g wants several gigabytes for the subgroup lattice of
# A11, and pentagonSearch.g runs six to thirteen minutes.  A scheduled CI job
# runs this weekly; a GAP upgrade is what it exists to catch.
verify-slow: ## Re-run the slow GAP computations (minutes; CI runs this on a schedule)
	@command -v gap > /dev/null || { \
	  echo "error: gap is not on PATH; run this inside 'nix develop'."; exit 2; }
	@test -f "$(FINLATREPGAP_DIR)/Hexagon.g" || { \
	  echo "error: no GAP programs at $(FINLATREPGAP_DIR); see verify-gap."; exit 2; }
	FINLATREPGAP_DIR="$(abspath $(FINLATREPGAP_DIR))" gap -q -b -A --quitonbreak -o 8g scripts/gap/verify-slow.g < /dev/null

test: test-utils test-finlatrep ## Run every test suite

# Through _utils/run_tests.py rather than unittest's own runner, so that
# every test prints one line saying what it tested and which file tested it.
test-utils: ## Run the shared functional primitives' tests
	cd $(PYTHON_DIR) && PYTHONPATH=. $(PYTHON) -m _utils.run_tests _utils

test-finlatrep: ## Run the catalog checker's tests
	cd $(PYTHON_DIR) && PYTHONPATH=. $(PYTHON) -m _utils.run_tests finlatrep

# All three scripts, not just one: the targets below run lint, populate and
# update, so a GHPROJECT_DIR holding only some of them would pass a
# single-script guard and then fail with a raw python file-not-found instead of
# the status 2 this promises.
_check-ghproject:
	@if [ -n "$(GHPROJECT_DIR)" ]; then \
	  for s in lint populate update; do \
	    test -f "$(GHPROJECT_DIR)/scripts/gh_project_$$s.py" || { \
	      echo "error: github-project engine not usable at $(GHPROJECT_DIR)"; \
	      echo "       missing scripts/gh_project_$$s.py"; \
	      echo "       clone williamdemeo/github-project there, or unset"; \
	      echo "       GHPROJECT_DIR to use the flake input"; \
	      exit 2; }; \
	  done; \
	fi

project-lint: _check-ghproject ## Check the plan file for structural defects
	$(GHPROJECT_LINT) $(PLAN)

project-populate-dry: _check-ghproject ## Preview what populate would create on GitHub
	$(GHPROJECT_POPULATE) --dry-run $(PLAN)

project-populate: _check-ghproject ## Create the plan's labels, milestones and issues on GitHub
	$(GHPROJECT_POPULATE) $(PLAN)

project-update: _check-ghproject ## Rewrite the plan's generated regions from GitHub
	$(GHPROJECT_UPDATE) $(PLAN)

project-update-check: _check-ghproject ## Fail if the plan and GitHub disagree
	$(GHPROJECT_UPDATE_CHECK) $(PLAN)

clean: ## Remove build products
	$(MAKE) -C article clean
	find $(PYTHON_DIR) -name '__pycache__' -type d -exec rm -rf {} +
	rm -rf $(BUILD)
