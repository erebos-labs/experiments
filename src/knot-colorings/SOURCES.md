# Sources and mathematical scope

Established mathematical results, implemented with AI assistance. Counts do not compute longitude polynomials or smooth sliceness. Source portions and version-specific limitations are identified below. No paper body or image is distributed.

- Józef H. Przytycki, *3-coloring and other elementary invariants of knots*. [Source 1](https://arxiv.org/html/math/0608172v1)
  Sections 1 and 2 excerpts: definition, invariance, linear structure and connected sums
- Sudipta Kolay, *Knot Colorings: Coloring and Goeritz matrices*. [Source 1](https://arxiv.org/html/1910.08044v1)
  Sections 1–4 and Proposition 8; basic crossing equations used, composite-modulus equivalence not relied on
  Caution: Proposition 8 overstates determinant divisibility over composite Z/nZ. Trefoil modulo 9 supplies a direct counterexample.
- Knot Atlas contributors; braid table credits Thomas Gittings, *Knot Atlas original diagram data and conventions*. [Source 1](https://katlas.org/wiki/3_1) · [Source 2](https://katlas.org/wiki/4_1) · [Source 3](https://katlas.org/wiki/K11n34) · [Source 4](https://katlas.org/wiki/K11n42) · [Source 5](https://katlas.org/wiki/Gauss_Codes) · [Source 6](https://katlas.org/wiki/Planar_Diagrams)
  Named knot Gauss/PD/braid data; sign and orientation conventions. Transcribed small factual inputs in source_data.json. No images copied.
  Caution: Mirror convention warnings retained; total counts compared without handedness claims.
- Lisa Piccirillo, *The Conway knot is not slice*. [Source 1](https://arxiv.org/html/1808.02923v1)
  Abstract, introduction and Theorem 1.1; not the full handle-calculus proof
- Michael Eisermann, *Knot colouring polynomials*. [Source 1](https://msp.org/pjm/2007/231-2/pjm-v231-n2-p04-p.pdf)
  Introduction, Sections 2B/2D and 3A excerpts; Examples 2.17 and 2.18 numerical counts reproduced. No longitude polynomial computed.
- Alexander Madaus, Maisie Newman, Heather M. Russell, *Dehn coloring and the dimer model for knots*. [Source 1](https://arxiv.org/html/1510.02023v1)
  Sections 2 and 3 excerpts, especially Corollary 3.3 and Theorem 3.6; not the later dimer algorithm
- Neungjoo Goh, Suah Jeong, Seungbin Oh, Hyungkee Yoo, *Fox p-Colorings as Fixed Points of Braid Representations*. [Source 1](https://arxiv.org/html/2608.29046v1)
  Sections 1–3; related-work overlap acknowledged. Determinant-only count statement not relied on.
  Caution: Introductory Col_p = p*gcd(p,det) is too broad for arbitrary knots: connected trefoils at p=3 give 27, not 9. Fixed-point theorem agrees with direct enumeration.
- Slavik Jablan, Louis H. Kauffman, Pedro Lopes (v1); later revisions add Jun Ge, *Equivalence Classes of Colorings: the Topological Viewpoint*. [Source 1](https://arxiv.org/html/1208.0993v1) · [Source 2](https://arxiv.org/html/1208.0993v3)
  Section 2.1: integer matrix operations, prime nullity and composite zero-divisor counts; v3 confirms the prime-nullity and composite zero-divisor statements
