# What does smoke tell a seed?

An educational source guide and three small reproducible calculations, built with AI assistance. Established plant research is credited below. The numerical examples are deliberately constructed; no seeds were grown and no receptor assay or expression analysis was reproduced.

## What an observation identifies

Whole smoke, purified karrikin, receptor binding, signaling activation, seed emergence and ecological fitness are different interventions or endpoints. Results about one do not automatically establish the others.

Two washout toys compare a retained chemical-associated state with a downstream committed state. The first assumes no loss of retained state. In the second, pulse length p creates q=1-exp(-p). A retained state starts at q and has competing germination/loss rates a,b. A chemical-free committed state is deliberately assigned q*a/(a+b), with conversion rate a+b. Both give G(T)=q*a/(a+b)*(1-exp(-(a+b)*T)). The responsive fraction in the second model is chosen to match the first: this is a constructed identifiability counterexample, not a fitted biological mechanism. Independent chemical/state measurements could distinguish them.

The dose calculation converts reported smoke-water KAR1 concentration 5.5 ±0.23 nmol/L to ideal dilution concentrations. Pure treatments 0.001–10 micromolar correspond to 1–10,000 nM. Whole smoke is not biologically equivalent to its KAR1 concentration; uncertainty notation is not interpreted as a confidence interval.

The minimal GEO-derived table contains sample design facts only. Its 28 two-channel arrays form seven comparisons, with balanced dye orientation. Deposited protocol describes two biological replicates plus dye swaps, and equal-RNA pooling of germinated/nongerminated achenes at 24 h. Four arrays are not four independent biological replicates, and pooled values do not identify the separate stage values. No raw expression table, personal contact metadata, differential-expression test or inferred replicate pairing is included.

## Run

Existing Python3 standard library only:

```sh
python3 -B verify.py
```

Checks include five dose checks, ten initial washout properties, 96 finite-loss cases, independent 2,000-step integrations at one setting, invalid-input controls, and design-table consistency. Numerical consistency does not validate the biological assumptions. The static page needs no JavaScript, backend or remote data. Rendered browser behavior is not established by these checks.

## Primary sources and limits

- [Nelson et al. (2009)](https://academic.oup.com/plphys/article/149/2/863/6107939): Arabidopsis light/GA context; do not generalize a universal light gate.
- [Gupta et al. (2019)](https://academic.oup.com/plphys/article/181/2/458/6000151): Grand Rapids lettuce dark germination under defined treatments; a different species/assay from Nelson.
- [Soós et al. (2012)](https://nph.onlinelibrary.wiley.com/doi/10.1111/j.1469-8137.2012.04358.x): washout, dose and transcript experiments inspired the toys. The toys do not refute the paper's combined evidence or identify the actual inhibitor target. Rainfall interpretation is an ecological hypothesis.
- [Kushihara et al. (2025)](https://www.pnas.org/doi/10.1073/pnas.2414779122): ligand binding and activation differ. The proposed activating dMGer adduct was not detected by denaturing MS; a stable Ser95 adduct of a different compound was antagonistic. Main text reviewed; supplementary spectra not independently assessed.
- [Sella Rolando et al. (2026)](https://www.nature.com/articles/s41598-025-30823-7): measured smoke-water concentration used in the unit conversion; no raw germination-data reanalysis.
- [GSE34642](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE34642): public series/sample design metadata, not expression results. Minimal derived fields are retained with accession identifiers; raw metadata and contact information are excluded.

Original implementation/presentation: Erebos Labs, with AI assistance. Citations retain their copyrights; no publication bodies, third-party images or libraries are bundled. See the repository copyright notice. No novelty or field-adaptation claim.
