# LaTeX Makefile
FILE=SmallLatticeReps
REFS=inputs/refs
AUX1=SmallLatticeReps
AUX2=inputs/macros.sty
AUX3=inputs/au.cls

all: $(FILE).pdf

.PHONY: clean

clean:
	rm -f *.aux *.out *.blg *.log $(FILE).bbl $(REFS).bib 

$(FILE).pdf: $(FILE).tex $(AUX2)
	rm -f $(REFS).bib
	pdflatex $(FILE).tex
	bibtex $(AUX1).aux
	pdflatex $(FILE).tex
	pdflatex $(FILE).tex

$(FILE).tex: $(AUX2) $(AUX3)

$(AUX3):
