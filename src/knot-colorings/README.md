# A knot can hide from every Fox color count

An educational Fox and finite-group coloring explorer. Established mathematics; no new invariant or theorem. Compare knots only under the same label set and crossing rule. Matching counts are inconclusive.

Run from this directory with existing Python 3 and Node.js:

    python3 -B build.py
    python3 -B -m unittest -v test_model test_groups
    python3 -B verify_certificates.py
    node test_engine.js

The build writes index.html and data/. Open index.html for the standalone explorer. Tests independently reconstruct the integer inverse and check matrix witnesses, reference counts, diagram identities and actual inline controllers under a minimal DOM stub. A stub does not establish browser layout, keyboard or assistive-technology behavior. No physical-device or universal knot-recognition claim.

The Conway and Kinoshita–Terasaka fixed-label counts reproduce Eisermann (2007), Examples 2.17–2.18. Knot Atlas mirror conventions are preserved; no handedness is assigned. Composite moduli are enumerated rather than treated as fields. See SOURCES.md for exact versions and printed-formula cautions.

No server, third-party runtime, analytics or automatic network requests. Source links open public references when followed. Built with AI assistance. See COPYRIGHT.txt and THIRD_PARTY_NOTICES.md.
