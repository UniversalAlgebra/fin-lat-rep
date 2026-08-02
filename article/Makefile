# LaTeX Makefile
FILE=SmallLatticeReps
REFS=inputs/refs
AUX1=SmallLatticeReps
AUX2=inputs/macros.sty
AUX3=inputs/au.cls

# Overridable so a non-interactive caller can add flags, e.g.
#   make PDFLATEX="pdflatex -interaction=nonstopmode -halt-on-error"
# Plain `make` behaves exactly as it always has.
PDFLATEX ?= pdflatex
BIBTEX ?= bibtex

all: $(FILE).pdf

.PHONY: clean

clean:
	rm -f *.aux *.out *.blg *.log $(FILE).bbl $(REFS).bib 

$(FILE).pdf: $(FILE).tex $(AUX2)
	rm -f $(REFS).bib
	$(PDFLATEX) $(FILE).tex
	$(BIBTEX) $(AUX1).aux
	$(PDFLATEX) $(FILE).tex
	$(PDFLATEX) $(FILE).tex

$(FILE).tex: $(AUX2) $(AUX3)

$(AUX3):
