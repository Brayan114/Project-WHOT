# WHOT-ML Paper 1 — LaTeX Manuscript Package

This directory contains the complete LaTeX source package for the preprint and publication of **WHOT-ML Paper 1**:

> **Title:** WHOT-ML: A Configurable Partially Observable Multi-Agent Environment for Machine Learning Research  
> **Author:** Brayan Osinka (Independent Researcher)  
> **Repository:** [https://github.com/Brayan114/Project-WHOT](https://github.com/Brayan114/Project-WHOT)  
> **Simulator Baseline:** WHOT-NG-v1.0 (commit 7c1a2dc)  
> **Production Dataset:** paper1_production_20261004_215724_7c1a2dc ( = 12,350$ runs)

---

## Directory Structure

`	ext
paper/
├── main.tex            # Full article LaTeX manuscript
├── references.bib      # Complete BibTeX bibliography (16 references)
├── README.md           # This compilation and usage guide
└── figures/            # Full-resolution empirical publication figures
    ├── fig1_characterization_full.png
    ├── fig2_partial_observability_full.png
    ├── fig3_baseline_winrates_full.png
    ├── fig4_player_scaling_full.png
    └── fig5_rule_variants_full.png
`

---

## Compilation Instructions

### Option A: Overleaf (Recommended)

1. Create a **New Project** on [Overleaf](https://www.overleaf.com/) -> **Upload Project**.
2. Upload the paper/ directory (or a ZIP archive containing main.tex, 
eferences.bib, and the igures/ folder).
3. Set the project compiler to **pdfLaTeX** or **XeLaTeX** (Menu -> Compiler).
4. Set the main document to main.tex.
5. Click **Recompile**.

### Option B: Local Command Line (TeX Live / MiKTeX / MacTeX)

Ensure a standard LaTeX distribution is installed with pdflatex and ibtex.

`ash
cd paper

# 1. First pass: scan structure and citations
pdflatex -interaction=nonstopmode main.tex

# 2. Compile bibliography
bibtex main

# 3. Second pass: resolve cross-references and citations
pdflatex -interaction=nonstopmode main.tex

# 4. Third pass: finalize page layout and table floats
pdflatex -interaction=nonstopmode main.tex
`

Or using latexmk:

`ash
cd paper
latexmk -pdf main.tex
`

---

## Artifact Verification

All 7 tables and 5 figures in main.tex preserve the exact empirical values and 95% Wilson confidence intervals verified during the Kaggle Cloud production run ( = 12,350$).
