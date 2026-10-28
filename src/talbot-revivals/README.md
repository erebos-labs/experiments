# The pattern that comes back

An educational comparison of quadratic paraxial propagation and exact forward scalar dispersion for a finite angular spectrum. The interactive page uses an infinite, monochromatic, coherent periodic input. Separate follow-on calculations examine incoherent source ensembles and finite smooth Gaussian arrays. These models are not combined.

Run from this directory using existing Python 3 and Node.js, without installing dependencies:

    python3 -B build.py
    python3 -B study.py
    python3 -B scaling.py
    python3 -B verify.py
    node verify.js
    node ui_smoke.js
    python3 -B coherence.py
    python3 -B verify_coherence.py
    python3 -B finite_array.py
    python3 -B verify_finite_array.py

Generated calculations go to data/. Open index.html for the interactive periodic-field explorer and study.html for the follow-on results. Numerical and synthetic DOM/canvas tests do not establish actual browser rendering, keyboard behavior or assistive-technology support. Figure pixels illustrate computed scalar intensity, not observations from an apparatus.

The full paraxial return distance is 2d²/λ. “Exact scalar” means dispersion for the stated finite scalar spectrum; no vector, evanescent, material or laboratory model. A high normalized overlap or shape score alone does not establish contrast recovery. Finite-array results use smooth Gaussian slots, not a hard rectangular aperture. See COHERENCE.md, FINITE-ARRAY.md and SOURCES.md for assumptions, counterexamples, source scope and convergence limits.

No server, third-party runtime, automatic network requests, analytics or saved user state. Public references open only when followed. Built with AI assistance. See COPYRIGHT.txt and THIRD_PARTY_NOTICES.md.
