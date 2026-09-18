# File: Makefile
#
# Front door for the repository.  It carries the paper, the catalog check from
# issue #29, the Universal Algebra Calculator's smoke test from issue #26, and
# the project targets from issue #27, which drive the github-project engine.
#
# Every target expects the development shell.  Run `nix develop` first: that
# is where pdflatex, uacalc and xvfb-run are, and nothing here asks you to
# install them yourself.  See CONTRIBUTING.md.

PYTHON ?= python3
PYTHON_DIR := scripts/python
ARTICLE := article/SmallLatticeReps.tex

# The algebras live in UACalc/AlgebraFiles, not here; see uacalc-files/README.md.
# Point ALGEBRA_FILE at a local checkout, or at any .ua file you want checked.
# Issue #25 replaces this with a pinned flake input, at which point the default
# stops depending on where a contributor happens to keep the checkout.
ALGEBRAFILES_DIR ?= $(HOME)/git/UACalc/AlgebraFiles/master
ALGEBRA_FILE ?= $(ALGEBRAFILES_DIR)/CongruenceLatReps/SmallLatticeReps.ua

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

.PHONY: help paper check-catalog uacalc-smoke test test-finlatrep test-utils \
        clean project-lint project-populate-dry project-populate \
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

test: test-utils test-finlatrep ## Run every test suite

test-utils: ## Run the shared functional primitives' tests
	cd $(PYTHON_DIR) && PYTHONPATH=. $(PYTHON) -m unittest discover -s _utils -p "test_*.py"

test-finlatrep: ## Run the catalog checker's tests
	cd $(PYTHON_DIR) && PYTHONPATH=. $(PYTHON) -m unittest discover -s finlatrep -p "test_*.py"

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
