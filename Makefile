# File: Makefile
#
# Front door for the repository.  Issue #27 adds the project targets that
# drive the github-project engine; this file currently carries the paper and
# the catalog check from issue #29.

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

.PHONY: help paper check-catalog test test-finlatrep test-utils clean

help: ## Show this help
	@grep -hE '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) \
	  | awk -F':.*?## ' '{printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

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

test: test-utils test-finlatrep ## Run every test suite

test-utils: ## Run the shared functional primitives' tests
	cd $(PYTHON_DIR) && PYTHONPATH=. $(PYTHON) -m unittest discover -s _utils -p "test_*.py"

test-finlatrep: ## Run the catalog checker's tests
	cd $(PYTHON_DIR) && PYTHONPATH=. $(PYTHON) -m unittest discover -s finlatrep -p "test_*.py"

clean: ## Remove build products
	$(MAKE) -C article clean
	find $(PYTHON_DIR) -name '__pycache__' -type d -exec rm -rf {} +
