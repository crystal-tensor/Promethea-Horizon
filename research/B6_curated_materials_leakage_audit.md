# B6 Curated Materials Leakage Audit v0

Status: `curated_retrospective_leakage_audit_not_material_discovery_claim`

This artifact upgrades B6 from a synthetic descriptor toy to a small curated
retrospective table with explicit time-split and family-prior leakage pressure.
It is not a material-discovery claim, not a solved high-Tc mechanism, and not a
complete superconductivity database.

## Dataset

- Records: 26
- Families: 12
- Split year: 2008
- Post-split records: 8
- High-Tc threshold: 30.0 K
- Source scope: small curated retrospective table; Tc values and family labels are for audit pressure, not a complete database

## Leakage Metrics

| Metric | Value |
|---|---:|
| All physics precision@10 | 0.900000 |
| All physics average precision@10 | 0.890000 |
| All random average precision@10 mean | 0.534594 |
| Post-split physics average precision | 0.909354 |
| Post-split family-prior average precision | 0.937925 |
| Post-split leaky combined average precision | 0.826020 |
| Leaky combined minus physics AP | -0.083333 |
| Family-holdout mean physics AP | 0.972222 |
| Family-holdout mean random AP | 0.852865 |

## Top Physics-Descriptor Rows

| Rank | Formula | Family | Year | Tc K | Pressure GPa | Score |
|---:|---|---|---:|---:|---:|---:|
| 1 | YBa2Cu3O7-d | cuprate | 1987 | 93.0 | 0.0 | 0.4529 |
| 2 | HgBa2Ca2Cu3O8+d | cuprate | 1993 | 134.0 | 0.0 | 0.4419 |
| 3 | HgBa2Ca2Cu3O8+d | cuprate | 1994 | 164.0 | 30.0 | 0.4419 |
| 4 | monolayer FeSe/SrTiO3 | iron_chalcogenide | 2012 | 65.0 | 0.0 | 0.4409 |
| 5 | Bi2Sr2CaCu2O8+x | cuprate | 1988 | 95.0 | 0.0 | 0.4340 |
| 6 | La2-xBaxCuO4 | cuprate | 1986 | 35.0 | 0.0 | 0.4211 |
| 7 | SmFeAsO1-xFx | iron_pnictide | 2008 | 55.0 | 0.0 | 0.4118 |
| 8 | Tl2Ba2Ca2Cu3O10 | cuprate | 1988 | 125.0 | 0.0 | 0.4044 |
| 9 | LaFeAsO1-xFx | iron_pnictide | 2008 | 26.0 | 0.0 | 0.3861 |
| 10 | FeSe | iron_chalcogenide | 2009 | 37.0 | 7.0 | 0.3808 |

## Post-Split Top Rows

| Rank | Formula | Family | Year | Tc K | Pressure GPa | Score |
|---:|---|---|---:|---:|---:|---:|
| 1 | monolayer FeSe/SrTiO3 | iron_chalcogenide | 2012 | 65.0 | 0.0 | 0.4409 |
| 2 | FeSe | iron_chalcogenide | 2009 | 37.0 | 7.0 | 0.3808 |
| 3 | La3Ni2O7 | nickelate | 2023 | 80.0 | 14.0 | 0.3157 |
| 4 | Nd1-xSrxNiO2 | nickelate | 2019 | 15.0 | 0.0 | 0.3122 |
| 5 | LaH10 | hydride | 2019 | 250.0 | 170.0 | 0.2393 |
| 6 | H3S | hydride | 2015 | 203.0 | 155.0 | 0.2308 |
| 7 | YH6 | hydride | 2021 | 224.0 | 166.0 | 0.2253 |
| 8 | CaH6 | hydride | 2022 | 215.0 | 170.0 | 0.2068 |

## Validation Errors

- none

## Interpretation

- The table is now real/curated enough to expose family and time leakage, but it
  is still much too small for material discovery.
- The descriptor ranking is evaluated against a family-prior baseline and a
  leaky family-combined score, so future B6 claims cannot hide behind family
  labels.
- The next B6 artifact must replace qualitative descriptor values with computed
  structural, electronic, and B5-linked observables.
