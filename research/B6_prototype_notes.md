# B6 Prototype Notes: High-Temperature Superconductivity Search v0.1

Last updated: 2026-06-13

Problem: **37. High-temperature superconductivity**

The sixth attack direction is now initialized with a toy descriptor-ranking
harness. This is not a material discovery claim. It is a scaffolding benchmark
for turning quantum-simulation-derived descriptors into candidate rankings and
for testing whether those rankings recover known high-temperature
superconducting families before moving to real materials databases.

## Current Components

- Benchmark manifest: `../benchmarks/B6_high_temperature_superconductivity.yaml`
- Descriptor ranker: `../tools/b6_superconductivity_descriptor_ranker.py`
- First result: `../results/B6_superconductivity_descriptor_ranker_v0.json`
- Curated leakage-audit script:
  `../tools/b6_curated_materials_leakage_audit.py`
- Curated leakage-audit result:
  `../results/B6_curated_materials_leakage_audit_v0.json`
- Curated leakage-audit report:
  `../research/B6_curated_materials_leakage_audit.md`

## Descriptor Model

The v0 model uses six toy candidate families:

1. `cuprate_like`
2. `iron_pnictide_like`
3. `hydride_like`
4. `nickelate_like`
5. `flat_band_oxide_like`
6. `organic_salt_like`

Each candidate is represented by coarse features:

- correlation ratio `U/W`
- spin fluctuation strength
- electron-phonon coupling proxy
- dimensionality
- disorder
- pressure cost
- carrier-density optimality
- competing-order strength

The ranking score combines a spin-fluctuation pairing descriptor, a phonon
pairing descriptor, carrier optimality, and penalties for disorder, competing
orders, and high pressure. An ensemble of perturbed weights gives a small
uncertainty estimate for active-learning priority.

## First Result

The first run covers 72 toy candidates and ranks the top 12. The benchmark
records:

- known high-Tc family precision at 12
- known high-Tc family recall at 12
- top family counts
- top candidate IDs
- descriptor uncertainty per candidate

Current v0 results:

| Metric | Value |
|---|---:|
| Candidates | 72 |
| Top-k | 12 |
| Known high-Tc precision@12 | 0.833333 |
| Known high-Tc recall@12 | 0.277778 |

Top-12 family counts:

| Family | Count |
|---|---:|
| `cuprate_like` | 8 |
| `iron_pnictide_like` | 2 |
| `nickelate_like` | 2 |

Interpretation:

- This creates a measurable B6 target before real materials data is connected.
- The desired behavior is not to prove a new material, but to recover known
  high-Tc families and identify where the descriptor is merely copying family
  priors.
- The v0 ranking recovers known cuprate-like and iron-pnictide-like candidates
  strongly, but hydride-like candidates are pushed down by the pressure penalty;
  that tradeoff should be tested rather than accepted as truth.
- The descriptor should eventually be replaced by outputs from B5-style
  Hubbard, plaquette, or electron-phonon solvers.

## Curated Materials Leakage Audit

T-B6-001 upgrades the B6 evidence from a synthetic candidate table to a small
curated retrospective materials table. It is still not a material discovery
claim, not a solved high-Tc mechanism, and not a complete superconductivity
database.

Current curated audit metrics:

| Metric | Value |
|---|---:|
| Records | 26 |
| Families | 12 |
| Split year | 2008 |
| Post-split records / positives | 8 / 7 |
| High-Tc threshold | 30 K |
| All physics AP@10 | 0.890000 |
| All random AP@10 mean | 0.534594 |
| Post-split physics AP | 0.909354 |
| Post-split family-prior AP | 0.937925 |
| Post-split random AP mean | 0.903048 |
| Family-holdout physics AP | 0.972222 |
| Family-holdout random AP | 0.852865 |
| Validation errors | 0 |

Interpretation:

- The audit now explicitly compares descriptor-only ranking with family-prior
  and leaky family-combined baselines.
- The post-split set is too small and too positive-heavy, so high post-split AP
  is not strong validation; it is a pressure test that exposes the need for more
  negative controls.
- The next serious B6 result must replace qualitative descriptors with computed
  structural/electronic features and B5-linked observables.

## Limits

- Candidates are synthetic, not actual compounds.
- The descriptor is hand-built and should be treated as a schema test.
- Known-family precision is not scientific validation; it is only a smoke test.
- No synthesis feasibility, toxicity, stability, or experimental uncertainty is
  modeled beyond a crude pressure/disorder penalty.

## Next Algorithmic Step

Build the first useful B6 comparison:

1. Replace qualitative descriptor values with computed structural/electronic
   descriptors.
2. Connect at least one descriptor to the B5 Hubbard/plaquette solver.
3. Expand post-2008 negative controls so random and family-prior baselines
   cannot saturate.
4. Run retrospective validation on known cuprate, pnictide, hydride, nickelate,
   and organic families with explicit family holdouts.
5. Track whether active learning chooses candidates that improve descriptor
   uncertainty rather than only reselecting obvious families.
