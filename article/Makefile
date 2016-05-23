# LaTeX Makefile
FILE=SmallLatticeReps
REFS=inputs/refs
AUX1=SmallLatticeReps

all: $(FILE).pdf

.PHONY: clean $(REFS).bib

clean:
	rm -f *.aux *.out *.blg *.log $(FILE).bbl $(REFS).bib 

$(FILE).pdf: $(FILE).tex
	rm -f $(REFS).bib
	pdflatex $(FILE).tex
	bibtex $(AUX1).aux
	pdflatex $(FILE).tex
	pdflatex $(FILE).tex
