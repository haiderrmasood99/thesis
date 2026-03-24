@echo off
echo Compiling final_experiments_report...
pdflatex main.tex
echo Recompiling to cross-reference TOC and Figure numbers...
pdflatex main.tex
echo Compilation complete.
pause
