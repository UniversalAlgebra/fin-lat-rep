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

GALLERY=inputs/tikz/gallery
# Every file under inputs/tikz: the pics, all.tex which inputs them, and the
# gallery's own source.  Both documents depend on the lot.
PICS := $(wildcard inputs/tikz/*.tex)

all: $(FILE).pdf

.PHONY: clean gallery

clean:
	rm -f *.aux *.out *.blg *.log $(FILE).bbl $(REFS).bib 
	rm -f $(GALLERY).pdf $(GALLERY).aux $(GALLERY).log $(GALLERY).out

# Every Hasse diagram side by side, one pic per entry, for the eye.  Run
# from this directory so that inputs/tikz/all.tex and the files it inputs
# resolve; -output-directory keeps the build products beside the source.
gallery: $(GALLERY).pdf

$(GALLERY).pdf: $(PICS) $(AUX2)
	$(PDFLATEX) -output-directory=inputs/tikz $(GALLERY).tex

# Every Hasse diagram is a pic file that all.tex inputs, so the PDF depends on
# all of them; without this, editing a lattice and running make leaves the old
# PDF in place and says "Nothing to be done".
$(FILE).pdf: $(FILE).tex $(AUX2) $(PICS)
	rm -f $(REFS).bib
	$(PDFLATEX) $(FILE).tex
	$(BIBTEX) $(AUX1).aux
	$(PDFLATEX) $(FILE).tex
	$(PDFLATEX) $(FILE).tex

$(FILE).tex: $(AUX2) $(AUX3)

$(AUX3):
