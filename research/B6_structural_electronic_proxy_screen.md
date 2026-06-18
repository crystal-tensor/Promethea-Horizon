# B6 Structural/Electronic Proxy Screen v0.1

- Status: structural_electronic_proxy_boundary_not_material_discovery_claim
- Method: b6_structural_electronic_proxy_screen_v0
- Model status: curated_structural_electronic_proxies_not_dft_or_crystallographic_database
- Records: 38
- Expanded negative controls: 12
- Families: 22
- Structural AP@12: 0.6110119047619047
- Formula AP@12: 0.09999999999999999
- Family-prior AP@12: 1.0
- Post-split structural AP: 0.6899659863945579
- Post-split family-prior AP: 0.9821428571428571
- Family-holdout structural mean AP: 0.8958333333333333
- Top-k negative-control count: 3
- Validation errors: []

## Interpretation

The structural/electronic proxy improves over formula-only ranking, but it still
does not beat the family-prior baseline and it promotes several negative controls.
This makes the artifact a useful leakage boundary rather than a discovery claim.

## Top Structural/Electronic Rows

| rank | material | formula | family | Tc K | source | score | dim | corr | spin | B5 response |
|---:|---|---|---|---:|---|---:|---:|---:|---:|---:|
| 1 | Hg1223_1993 | HgBa2Ca2Cu3O8+d | cuprate | 134.0 | curated | 2.7515 | 2.00 | 0.910 | 0.830 | 0.887 |
| 2 | CuO_negative | CuO | binary_oxide_negative | 0.0 | negative_control | 2.6799 | 2.00 | 0.945 | 0.827 | 0.898 |
| 3 | Bi2212_1988 | Bi2Sr2CaCu2O8+x | cuprate | 95.0 | curated | 2.6760 | 2.00 | 0.900 | 0.820 | 0.877 |
| 4 | YBCO_1987 | YBa2Cu3O7-d | cuprate | 93.0 | curated | 2.6749 | 2.10 | 0.900 | 0.840 | 0.877 |
| 5 | LBCO_1986 | La2-xBaxCuO4 | cuprate | 35.0 | curated | 2.6730 | 2.00 | 0.920 | 0.860 | 0.895 |
| 6 | Tl2223_1988 | Tl2Ba2Ca2Cu3O10 | cuprate | 125.0 | curated | 2.5720 | 2.00 | 0.900 | 0.800 | 0.868 |
| 7 | Hg1223_pressure_1994 | HgBa2Ca2Cu3O8+d | cuprate | 164.0 | curated | 2.4515 | 2.00 | 0.910 | 0.830 | 0.887 |
| 8 | monolayer_FeSe_STO_2012 | monolayer FeSe/SrTiO3 | iron_chalcogenide | 65.0 | curated | 2.3580 | 2.00 | 0.740 | 0.740 | 0.757 |
| 9 | PrNiO2_parent_negative | PrNiO2 | nickelate_parent_negative | 0.0 | negative_control | 2.3373 | 2.00 | 0.786 | 0.425 | 0.706 |
| 10 | SmFeAsOF_2008 | SmFeAsO1-xFx | iron_pnictide | 55.0 | curated | 2.3069 | 2.10 | 0.700 | 0.780 | 0.748 |
| 11 | LaFeAsOF_2008 | LaFeAsO1-xFx | iron_pnictide | 26.0 | curated | 2.2589 | 2.10 | 0.680 | 0.740 | 0.724 |
| 12 | BaKFe2As2_2008 | Ba1-xKxFe2As2 | iron_pnictide | 38.0 | curated | 2.2157 | 2.20 | 0.680 | 0.760 | 0.722 |

## Claim Boundary

- material_discovery_claimed: False
- mechanism_solved: False
- complete_materials_database: False
- computed_quantum_observable_claimed: False
- real_dft_claimed: False
- real_crystallographic_database_claimed: False
- uses_formula_derived_descriptors: False
- uses_structural_electronic_proxies: True
- uses_b5_linked_proxy: True
- what_is_supported: Curated structural/electronic proxy channels improve over formula-only ranking, while exposing remaining family-prior leakage and top-k negative-control pressure.
- what_is_not_supported: This is not a material discovery, solved high-Tc mechanism, complete database, real DFT calculation, crystallographic database pull, or computed quantum observable.

## Next Gate

Replace these curated proxy channels with actual crystallographic, DFT, or
B5-computed structural/electronic observables, then expand post-2008 negatives
until family priors and random baselines can no longer saturate the audit.
