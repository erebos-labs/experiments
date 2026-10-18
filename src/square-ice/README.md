# Square ice: boundaries, loops and counts

This is a source-and-derivation module, not an interactive app. Python 3.10 or later is required. Library imports do not create output directories. Executed checks write into output/ and need a writable checkout; their timestamps use standard-library UTC without an external timezone database. No package installation is required.

Run `python3 -B checks.py`, `python3 -B verify_loops.py`, `python3 -B boundary_paths.py`, `python3 -B test_soft_bound.py` and `python3 -B test_review.py`. The included ASM sweep covers n=1..10; independent soft defect polynomials cover n=2,3. `python3 -B soft_ice.py --max-n 8` runs the bounded soft-constraint sweep. Public counting entry points validate dimensions before expensive work: row/domain widths and heights at most 14, free width at most 10 and periodic width at most 6. Those limits are not a fast-runtime or low-memory guarantee at every endpoint. A(0)=1 is the explicit empty-ASM convention; negative sizes are rejected.

The six n=14 samples use seed 1967. Reconstruct them with `python3 -B generate_fixtures.py`; add `--check` for a non-writing byte comparison. Generation verifies the n=14 total separately, not all intermediate sizes. Canonical metadata binds the generator hash; PROVENANCE.json records fixture/source hashes and the actual tested toolchain.

Optional loop replay needs Clang with C++20 and its unsigned __int128 extension; MSVC/Windows portability is not claimed. Create output/, compile `clang++ -std=c++20 -O2 -Wall -Wextra -Werror loops.cpp -o output/loops`, and save `./output/loops > output/loops-run.jsonl`. Then run `python3 -B generate_fixtures.py --loop-output output/loops-run.jsonl --check`. Canonical nine-row data omits nondeterministic seconds; raw timing remains in output/.

## Numerical and scientific limits

The soft partition function uses integers at q=0 or q=1. For interior q it conservatively rejects parameters when n² log(q) is below log(sys.float_info.min), preventing the demonstrated false positive-q zero from term underflow. This bounded binary64 calculation is still approximate. The CLI sweep is limited to n≤8. Mathematical positivity and boundary-limit arguments are separate from floating-point accuracy.

An equally weighted arrow model is not a quantitative water-ice model. Exact finite checks, authored derivations and cited thermodynamic results are distinguished. No general proof verification or novelty claim. The unfinished strip-bound extension is absent. AI assistance is acknowledged; existing copyright and third-party rights apply. Finite checks do not constitute independent theorem, source or empirical verification.

Validation scripts reject Python -O and PYTHONOPTIMIZE before reporting results. Internal model consistency checks remain always on. Loop fixtures require exactly the nine unique cases torus n=2..5 and free n=2..6, with the expected scientific fields; duplicates, omissions and extra fields fail. Seeded fixture byte reproduction was exercised on Python 3.14.7 only; Python 3.10+ syntax/runtime support is not a cross-version PRNG-sequence guarantee. VALIDATION.json contains inspectable normalized local check results.
