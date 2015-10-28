# sanify-latex
Pretty-prints the output from pdflatex. It combines broken lines, uses color highlighting, and connects messages with the file it was generated from. This makes it much easier to spot warnings, and understand the context they appear in.

## Usage
You can use sanify in the two following ways:

```pdflatex main.tex | ./sanify-latex.py```
Pipe the output of pdflatex into sanify-latex. It is highly recormened to run pdflatex with `-interaction=nonstopmode`.

```./sanify-latex.py main.tex```
sanify-latex runs pdflatex with its supplied parameters, and the following parameters: `-interaction=nonstopmode` `-halt-on-error` and `-synctex=1`.

## Disclaimer

sanify-latex tries to parse the output, but I expect LaTeX to always be able to find a way to mess it up as it looks like packages can essencially output whatever they want to. If you experince pdflatex outputting something sanify-latex cannot handle properly, save the output of pdflatex in a file and create an issue on the issue tracker. I will try to see if I can fix it.

## Dependencies
colorama

