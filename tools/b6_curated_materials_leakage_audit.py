#!/usr/bin/env python3
"""Curated retrospective B6 materials table with family/time leakage audit."""

from __future__ import annotations

import argparse
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean


MATERIALS = [
    {
        "material_id": "A15_Nb3Ge_1973",
        "formula": "Nb3Ge",
        "family": "a15_conventional",
        "discovery_year": 1973,
        "tc_k": 23.2,
        "pressure_gpa": 0.0,
        "correlation_strength": 0.25,
        "spin_fluctuation": 0.15,
        "phonon_lambda": 0.72,
        "dimensionality": 3.0,
        "carrier_tunability": 0.35,
        "disorder_risk": 0.20,
        "competing_order": 0.15,
        "source_lineage": "classic A15 superconductivity record",
    },
    {
        "material_id": "BKBO_1988",
        "formula": "Ba1-xKxBiO3",
        "family": "bismuthate",
        "discovery_year": 1988,
        "tc_k": 30.0,
        "pressure_gpa": 0.0,
        "correlation_strength": 0.45,
        "spin_fluctuation": 0.22,
        "phonon_lambda": 0.62,
        "dimensionality": 3.0,
        "carrier_tunability": 0.55,
        "disorder_risk": 0.34,
        "competing_order": 0.24,
        "source_lineage": "retrospective oxide high-Tc comparison",
    },
    {
        "material_id": "MgB2_2001",
        "formula": "MgB2",
        "family": "diboride",
        "discovery_year": 2001,
        "tc_k": 39.0,
        "pressure_gpa": 0.0,
        "correlation_strength": 0.18,
        "spin_fluctuation": 0.10,
        "phonon_lambda": 0.88,
        "dimensionality": 2.6,
        "carrier_tunability": 0.42,
        "disorder_risk": 0.18,
        "competing_order": 0.08,
        "source_lineage": "MgB2 phonon-mediated high-Tc milestone",
    },
    {
        "material_id": "K3C60_1991",
        "formula": "K3C60",
        "family": "fulleride",
        "discovery_year": 1991,
        "tc_k": 19.0,
        "pressure_gpa": 0.0,
        "correlation_strength": 0.70,
        "spin_fluctuation": 0.25,
        "phonon_lambda": 0.60,
        "dimensionality": 3.0,
        "carrier_tunability": 0.45,
        "disorder_risk": 0.25,
        "competing_order": 0.20,
        "source_lineage": "alkali fulleride superconductivity lineage",
    },
    {
        "material_id": "Cs3C60_2008",
        "formula": "Cs3C60",
        "family": "fulleride",
        "discovery_year": 2008,
        "tc_k": 38.0,
        "pressure_gpa": 0.7,
        "correlation_strength": 0.85,
        "spin_fluctuation": 0.35,
        "phonon_lambda": 0.68,
        "dimensionality": 3.0,
        "carrier_tunability": 0.38,
        "disorder_risk": 0.28,
        "competing_order": 0.28,
        "source_lineage": "pressure-tuned fulleride high-Tc record",
    },
    {
        "material_id": "kappa_BEDT_1990",
        "formula": "kappa-(BEDT-TTF)2Cu(NCS)2",
        "family": "organic",
        "discovery_year": 1990,
        "tc_k": 10.4,
        "pressure_gpa": 0.0,
        "correlation_strength": 0.82,
        "spin_fluctuation": 0.55,
        "phonon_lambda": 0.32,
        "dimensionality": 1.7,
        "carrier_tunability": 0.30,
        "disorder_risk": 0.35,
        "competing_order": 0.52,
        "source_lineage": "organic charge-transfer salt lineage",
    },
    {
        "material_id": "CeCoIn5_2001",
        "formula": "CeCoIn5",
        "family": "heavy_fermion",
        "discovery_year": 2001,
        "tc_k": 2.3,
        "pressure_gpa": 0.0,
        "correlation_strength": 0.95,
        "spin_fluctuation": 0.70,
        "phonon_lambda": 0.16,
        "dimensionality": 2.2,
        "carrier_tunability": 0.25,
        "disorder_risk": 0.28,
        "competing_order": 0.66,
        "source_lineage": "heavy-fermion unconventional superconductor",
    },
    {
        "material_id": "Sr2RuO4_1994",
        "formula": "Sr2RuO4",
        "family": "ruthenate",
        "discovery_year": 1994,
        "tc_k": 1.5,
        "pressure_gpa": 0.0,
        "correlation_strength": 0.62,
        "spin_fluctuation": 0.48,
        "phonon_lambda": 0.22,
        "dimensionality": 2.0,
        "carrier_tunability": 0.20,
        "disorder_risk": 0.22,
        "competing_order": 0.42,
        "source_lineage": "layered ruthenate unconventional lineage",
    },
    {
        "material_id": "LBCO_1986",
        "formula": "La2-xBaxCuO4",
        "family": "cuprate",
        "discovery_year": 1986,
        "tc_k": 35.0,
        "pressure_gpa": 0.0,
        "correlation_strength": 0.92,
        "spin_fluctuation": 0.86,
        "phonon_lambda": 0.26,
        "dimensionality": 2.0,
        "carrier_tunability": 0.82,
        "disorder_risk": 0.28,
        "competing_order": 0.52,
        "source_lineage": "Bednorz-Muller cuprate discovery lineage",
    },
    {
        "material_id": "YBCO_1987",
        "formula": "YBa2Cu3O7-d",
        "family": "cuprate",
        "discovery_year": 1987,
        "tc_k": 93.0,
        "pressure_gpa": 0.0,
        "correlation_strength": 0.90,
        "spin_fluctuation": 0.84,
        "phonon_lambda": 0.25,
        "dimensionality": 2.1,
        "carrier_tunability": 0.86,
        "disorder_risk": 0.22,
        "competing_order": 0.46,
        "source_lineage": "90 K cuprate milestone",
    },
    {
        "material_id": "Bi2212_1988",
        "formula": "Bi2Sr2CaCu2O8+x",
        "family": "cuprate",
        "discovery_year": 1988,
        "tc_k": 95.0,
        "pressure_gpa": 0.0,
        "correlation_strength": 0.90,
        "spin_fluctuation": 0.82,
        "phonon_lambda": 0.25,
        "dimensionality": 2.0,
        "carrier_tunability": 0.84,
        "disorder_risk": 0.24,
        "competing_order": 0.48,
        "source_lineage": "Bi-based cuprate lineage",
    },
    {
        "material_id": "Tl2223_1988",
        "formula": "Tl2Ba2Ca2Cu3O10",
        "family": "cuprate",
        "discovery_year": 1988,
        "tc_k": 125.0,
        "pressure_gpa": 0.0,
        "correlation_strength": 0.90,
        "spin_fluctuation": 0.80,
        "phonon_lambda": 0.24,
        "dimensionality": 2.0,
        "carrier_tunability": 0.82,
        "disorder_risk": 0.32,
        "competing_order": 0.50,
        "source_lineage": "Tl-based cuprate high-Tc lineage",
    },
    {
        "material_id": "Hg1223_1993",
        "formula": "HgBa2Ca2Cu3O8+d",
        "family": "cuprate",
        "discovery_year": 1993,
        "tc_k": 134.0,
        "pressure_gpa": 0.0,
        "correlation_strength": 0.91,
        "spin_fluctuation": 0.83,
        "phonon_lambda": 0.24,
        "dimensionality": 2.0,
        "carrier_tunability": 0.86,
        "disorder_risk": 0.20,
        "competing_order": 0.45,
        "source_lineage": "Hg-based ambient-pressure cuprate record lineage",
    },
    {
        "material_id": "Hg1223_pressure_1994",
        "formula": "HgBa2Ca2Cu3O8+d",
        "family": "cuprate",
        "discovery_year": 1994,
        "tc_k": 164.0,
        "pressure_gpa": 30.0,
        "correlation_strength": 0.91,
        "spin_fluctuation": 0.83,
        "phonon_lambda": 0.24,
        "dimensionality": 2.0,
        "carrier_tunability": 0.86,
        "disorder_risk": 0.20,
        "competing_order": 0.45,
        "source_lineage": "pressurized Hg cuprate record lineage",
    },
    {
        "material_id": "LaFeAsOF_2008",
        "formula": "LaFeAsO1-xFx",
        "family": "iron_pnictide",
        "discovery_year": 2008,
        "tc_k": 26.0,
        "pressure_gpa": 0.0,
        "correlation_strength": 0.68,
        "spin_fluctuation": 0.74,
        "phonon_lambda": 0.30,
        "dimensionality": 2.1,
        "carrier_tunability": 0.70,
        "disorder_risk": 0.26,
        "competing_order": 0.38,
        "source_lineage": "iron-pnictide discovery lineage",
    },
    {
        "material_id": "SmFeAsOF_2008",
        "formula": "SmFeAsO1-xFx",
        "family": "iron_pnictide",
        "discovery_year": 2008,
        "tc_k": 55.0,
        "pressure_gpa": 0.0,
        "correlation_strength": 0.70,
        "spin_fluctuation": 0.78,
        "phonon_lambda": 0.30,
        "dimensionality": 2.1,
        "carrier_tunability": 0.72,
        "disorder_risk": 0.28,
        "competing_order": 0.40,
        "source_lineage": "rare-earth iron-pnictide high-Tc lineage",
    },
    {
        "material_id": "BaKFe2As2_2008",
        "formula": "Ba1-xKxFe2As2",
        "family": "iron_pnictide",
        "discovery_year": 2008,
        "tc_k": 38.0,
        "pressure_gpa": 0.0,
        "correlation_strength": 0.68,
        "spin_fluctuation": 0.76,
        "phonon_lambda": 0.28,
        "dimensionality": 2.2,
        "carrier_tunability": 0.70,
        "disorder_risk": 0.25,
        "competing_order": 0.40,
        "source_lineage": "122 iron-pnictide lineage",
    },
    {
        "material_id": "FeSe_2008",
        "formula": "FeSe",
        "family": "iron_chalcogenide",
        "discovery_year": 2008,
        "tc_k": 8.0,
        "pressure_gpa": 0.0,
        "correlation_strength": 0.72,
        "spin_fluctuation": 0.70,
        "phonon_lambda": 0.26,
        "dimensionality": 2.1,
        "carrier_tunability": 0.55,
        "disorder_risk": 0.24,
        "competing_order": 0.34,
        "source_lineage": "iron-chalcogenide lineage",
    },
    {
        "material_id": "FeSe_pressure_2009",
        "formula": "FeSe",
        "family": "iron_chalcogenide",
        "discovery_year": 2009,
        "tc_k": 37.0,
        "pressure_gpa": 7.0,
        "correlation_strength": 0.72,
        "spin_fluctuation": 0.72,
        "phonon_lambda": 0.26,
        "dimensionality": 2.1,
        "carrier_tunability": 0.58,
        "disorder_risk": 0.24,
        "competing_order": 0.34,
        "source_lineage": "pressure-enhanced FeSe lineage",
    },
    {
        "material_id": "monolayer_FeSe_STO_2012",
        "formula": "monolayer FeSe/SrTiO3",
        "family": "iron_chalcogenide",
        "discovery_year": 2012,
        "tc_k": 65.0,
        "pressure_gpa": 0.0,
        "correlation_strength": 0.74,
        "spin_fluctuation": 0.74,
        "phonon_lambda": 0.40,
        "dimensionality": 2.0,
        "carrier_tunability": 0.68,
        "disorder_risk": 0.38,
        "competing_order": 0.32,
        "source_lineage": "interface-enhanced FeSe/STO lineage",
    },
    {
        "material_id": "H3S_2015",
        "formula": "H3S",
        "family": "hydride",
        "discovery_year": 2015,
        "tc_k": 203.0,
        "pressure_gpa": 155.0,
        "correlation_strength": 0.22,
        "spin_fluctuation": 0.14,
        "phonon_lambda": 0.98,
        "dimensionality": 3.0,
        "carrier_tunability": 0.45,
        "disorder_risk": 0.14,
        "competing_order": 0.08,
        "source_lineage": "compressed sulfur hydride high-Tc lineage",
    },
    {
        "material_id": "LaH10_2019",
        "formula": "LaH10",
        "family": "hydride",
        "discovery_year": 2019,
        "tc_k": 250.0,
        "pressure_gpa": 170.0,
        "correlation_strength": 0.18,
        "spin_fluctuation": 0.10,
        "phonon_lambda": 1.05,
        "dimensionality": 3.0,
        "carrier_tunability": 0.42,
        "disorder_risk": 0.12,
        "competing_order": 0.06,
        "source_lineage": "superhydride high-pressure record lineage",
    },
    {
        "material_id": "YH6_2021",
        "formula": "YH6",
        "family": "hydride",
        "discovery_year": 2021,
        "tc_k": 224.0,
        "pressure_gpa": 166.0,
        "correlation_strength": 0.18,
        "spin_fluctuation": 0.10,
        "phonon_lambda": 1.00,
        "dimensionality": 3.0,
        "carrier_tunability": 0.40,
        "disorder_risk": 0.12,
        "competing_order": 0.06,
        "source_lineage": "yttrium superhydride lineage",
    },
    {
        "material_id": "CaH6_2022",
        "formula": "CaH6",
        "family": "hydride",
        "discovery_year": 2022,
        "tc_k": 215.0,
        "pressure_gpa": 170.0,
        "correlation_strength": 0.18,
        "spin_fluctuation": 0.10,
        "phonon_lambda": 0.96,
        "dimensionality": 3.0,
        "carrier_tunability": 0.38,
        "disorder_risk": 0.13,
        "competing_order": 0.06,
        "source_lineage": "calcium hydride high-pressure lineage",
    },
    {
        "material_id": "NdNiO2_Sr_2019",
        "formula": "Nd1-xSrxNiO2",
        "family": "nickelate",
        "discovery_year": 2019,
        "tc_k": 15.0,
        "pressure_gpa": 0.0,
        "correlation_strength": 0.82,
        "spin_fluctuation": 0.62,
        "phonon_lambda": 0.22,
        "dimensionality": 2.0,
        "carrier_tunability": 0.55,
        "disorder_risk": 0.42,
        "competing_order": 0.50,
        "source_lineage": "infinite-layer nickelate lineage",
    },
    {
        "material_id": "La3Ni2O7_pressure_2023",
        "formula": "La3Ni2O7",
        "family": "nickelate",
        "discovery_year": 2023,
        "tc_k": 80.0,
        "pressure_gpa": 14.0,
        "correlation_strength": 0.86,
        "spin_fluctuation": 0.68,
        "phonon_lambda": 0.24,
        "dimensionality": 2.3,
        "carrier_tunability": 0.62,
        "disorder_risk": 0.36,
        "competing_order": 0.48,
        "source_lineage": "pressurized bilayer nickelate lineage",
    },
]


def physics_score(row: dict) -> float:
    dimensionality_bonus = math.exp(-((row["dimensionality"] - 2.05) ** 2) / 0.55)
    spin_channel = (
        row["spin_fluctuation"]
        * dimensionality_bonus
        * math.exp(-abs(row["correlation_strength"] - 0.82) / 0.55)
    )
    phonon_channel = row["phonon_lambda"] * (0.65 + 0.35 * (row["dimensionality"] / 3.0))
    carrier_channel = row["carrier_tunability"] * math.exp(-abs(row["correlation_strength"] - 0.75) / 0.90)
    pressure_penalty = max(row["pressure_gpa"] - 40.0, 0.0) / 180.0
    return (
        0.48 * spin_channel
        + 0.30 * phonon_channel
        + 0.20 * carrier_channel
        - 0.16 * (row["disorder_risk"] ** 1.25)
        - 0.18 * row["competing_order"]
        - 0.14 * pressure_penalty
    )


def high_tc(row: dict, threshold: float) -> bool:
    return float(row["tc_k"]) >= threshold


def precision_at_k(rows: list[dict], score_key: str, k: int, threshold: float) -> float:
    ranked = sorted(rows, key=lambda item: item[score_key], reverse=True)[:k]
    if not ranked:
        return 0.0
    return sum(1 for row in ranked if high_tc(row, threshold)) / len(ranked)


def recall_at_k(rows: list[dict], score_key: str, k: int, threshold: float) -> float:
    positives = sum(1 for row in rows if high_tc(row, threshold))
    if positives == 0:
        return 0.0
    ranked = sorted(rows, key=lambda item: item[score_key], reverse=True)[:k]
    return sum(1 for row in ranked if high_tc(row, threshold)) / positives


def average_precision_at_k(rows: list[dict], score_key: str, k: int, threshold: float) -> float:
    ranked = sorted(rows, key=lambda item: item[score_key], reverse=True)[:k]
    hits = 0
    precisions = []
    for idx, row in enumerate(ranked, start=1):
        if high_tc(row, threshold):
            hits += 1
            precisions.append(hits / idx)
    positives = sum(1 for row in rows if high_tc(row, threshold))
    if positives == 0:
        return 0.0
    return sum(precisions) / min(positives, k)


def family_rates(rows: list[dict], threshold: float) -> dict[str, float]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[row["family"]].append(row)
    global_rate = sum(1 for row in rows if high_tc(row, threshold)) / max(1, len(rows))
    rates = {"__global__": global_rate}
    for family, family_rows in grouped.items():
        rates[family] = sum(1 for row in family_rows if high_tc(row, threshold)) / len(family_rows)
    return rates


def random_precision(rows: list[dict], k: int, threshold: float, trials: int, seed: int) -> dict:
    rng = random.Random(seed)
    precisions = []
    aps = []
    for _ in range(trials):
        shuffled = list(rows)
        rng.shuffle(shuffled)
        ranked = shuffled[:k]
        precisions.append(sum(1 for row in ranked if high_tc(row, threshold)) / max(1, len(ranked)))
        hits = 0
        hit_precisions = []
        for idx, row in enumerate(ranked, start=1):
            if high_tc(row, threshold):
                hits += 1
                hit_precisions.append(hits / idx)
        positives = sum(1 for row in rows if high_tc(row, threshold))
        aps.append(sum(hit_precisions) / min(max(1, positives), k))
    return {"precision_at_k_mean": mean(precisions), "average_precision_at_k_mean": mean(aps)}


def annotate_scores(rows: list[dict], threshold: float, split_year: int) -> list[dict]:
    train_rows = [row for row in rows if row["discovery_year"] <= split_year]
    rates = family_rates(train_rows, threshold)
    annotated = []
    for row in rows:
        family_prior = rates.get(row["family"], rates["__global__"])
        physics = physics_score(row)
        enriched = {
            **row,
            "high_tc_label": high_tc(row, threshold),
            "time_split": "train" if row["discovery_year"] <= split_year else "post_split",
            "physics_descriptor_score": physics,
            "family_prior_score": family_prior,
            "leaky_family_combined_score": 0.55 * family_prior + 0.45 * physics,
        }
        annotated.append(enriched)
    return annotated


def family_holdout(rows: list[dict], k: int, threshold: float, seed: int) -> dict:
    families = sorted({row["family"] for row in rows})
    holdouts = []
    for family in families:
        test_rows = [row for row in rows if row["family"] == family]
        if len(test_rows) < 2:
            continue
        rand = random_precision(test_rows, min(k, len(test_rows)), threshold, 256, seed + len(holdouts))
        holdouts.append(
            {
                "heldout_family": family,
                "test_count": len(test_rows),
                "positive_count": sum(1 for row in test_rows if high_tc(row, threshold)),
                "physics_precision_at_k": precision_at_k(test_rows, "physics_descriptor_score", min(k, len(test_rows)), threshold),
                "physics_average_precision_at_k": average_precision_at_k(
                    test_rows, "physics_descriptor_score", min(k, len(test_rows)), threshold
                ),
                "random_precision_at_k_mean": rand["precision_at_k_mean"],
                "random_average_precision_at_k_mean": rand["average_precision_at_k_mean"],
            }
        )
    return {
        "holdout_count": len(holdouts),
        "mean_physics_average_precision_at_k": mean([row["physics_average_precision_at_k"] for row in holdouts]),
        "mean_random_average_precision_at_k": mean([row["random_average_precision_at_k_mean"] for row in holdouts]),
        "rows": holdouts,
    }


def top_rows(rows: list[dict], score_key: str, k: int) -> list[dict]:
    keep = [
        "rank",
        "material_id",
        "formula",
        "family",
        "discovery_year",
        "tc_k",
        "pressure_gpa",
        "high_tc_label",
        "physics_descriptor_score",
        "family_prior_score",
        "leaky_family_combined_score",
    ]
    ranked = sorted(rows, key=lambda item: item[score_key], reverse=True)[:k]
    out = []
    for idx, row in enumerate(ranked, start=1):
        copied = {key: row[key] for key in keep if key in row}
        copied["rank"] = idx
        out.append(copied)
    return out


def run(top_k: int, split_year: int, threshold: float, seed: int) -> dict:
    rows = annotate_scores(MATERIALS, threshold, split_year)
    train_rows = [row for row in rows if row["discovery_year"] <= split_year]
    post_rows = [row for row in rows if row["discovery_year"] > split_year]
    random_all = random_precision(rows, top_k, threshold, 512, seed)
    random_post = random_precision(post_rows, min(top_k, len(post_rows)), threshold, 512, seed + 1)

    top_all = top_rows(rows, "physics_descriptor_score", top_k)
    top_post = top_rows(post_rows, "physics_descriptor_score", min(top_k, len(post_rows)))
    top_family_counts = dict(Counter(row["family"] for row in top_all))
    top_post_family_counts = dict(Counter(row["family"] for row in top_post))

    physics_ap_post = average_precision_at_k(post_rows, "physics_descriptor_score", min(top_k, len(post_rows)), threshold)
    leaky_ap_post = average_precision_at_k(post_rows, "leaky_family_combined_score", min(top_k, len(post_rows)), threshold)
    family_prior_ap_post = average_precision_at_k(post_rows, "family_prior_score", min(top_k, len(post_rows)), threshold)
    leakage_delta = leaky_ap_post - physics_ap_post
    holdout = family_holdout(rows, max(2, min(4, top_k)), threshold, seed + 10)

    validation_errors = []
    if len(rows) < 24:
        validation_errors.append("curated table must contain at least 24 rows")
    if len({row["family"] for row in rows}) < 8:
        validation_errors.append("curated table must contain at least 8 material families")
    if not post_rows:
        validation_errors.append("post-split test set is empty")
    if any("family" not in row or "tc_k" not in row for row in rows):
        validation_errors.append("curated rows must include family and Tc")
    if family_prior_ap_post >= physics_ap_post and leakage_delta > 0.20:
        validation_errors.append("family-prior leakage dominates post-split physics score")

    return {
        "benchmark_id": "B6",
        "method": "b6_curated_materials_leakage_audit_v0",
        "status": "curated_retrospective_leakage_audit_not_material_discovery_claim",
        "model_status": "curated_materials_table_with_time_family_leakage_audit",
        "source_scope": "small curated retrospective table; Tc values and family labels are for audit pressure, not a complete database",
        "split_year": split_year,
        "high_tc_threshold_k": threshold,
        "record_count": len(rows),
        "family_count": len({row["family"] for row in rows}),
        "post_split_record_count": len(post_rows),
        "post_split_positive_count": sum(1 for row in post_rows if high_tc(row, threshold)),
        "metrics": {
            "all_physics_precision_at_k": precision_at_k(rows, "physics_descriptor_score", top_k, threshold),
            "all_physics_recall_at_k": recall_at_k(rows, "physics_descriptor_score", top_k, threshold),
            "all_physics_average_precision_at_k": average_precision_at_k(rows, "physics_descriptor_score", top_k, threshold),
            "all_random_precision_at_k_mean": random_all["precision_at_k_mean"],
            "all_random_average_precision_at_k_mean": random_all["average_precision_at_k_mean"],
            "post_split_physics_precision_at_k": precision_at_k(
                post_rows, "physics_descriptor_score", min(top_k, len(post_rows)), threshold
            ),
            "post_split_physics_average_precision_at_k": physics_ap_post,
            "post_split_family_prior_average_precision_at_k": family_prior_ap_post,
            "post_split_leaky_family_combined_average_precision_at_k": leaky_ap_post,
            "post_split_random_precision_at_k_mean": random_post["precision_at_k_mean"],
            "post_split_random_average_precision_at_k_mean": random_post["average_precision_at_k_mean"],
            "leaky_family_combined_minus_physics_ap": leakage_delta,
            "family_holdout_mean_physics_ap": holdout["mean_physics_average_precision_at_k"],
            "family_holdout_mean_random_ap": holdout["mean_random_average_precision_at_k"],
        },
        "top_k": top_k,
        "top_family_counts": top_family_counts,
        "top_post_split_family_counts": top_post_family_counts,
        "top_physics_rows": top_all,
        "top_post_split_physics_rows": top_post,
        "family_holdout": holdout,
        "materials_table": rows,
        "validation_errors": validation_errors,
        "claim_boundary": {
            "material_discovery_claimed": False,
            "mechanism_solved": False,
            "complete_materials_database": False,
            "physics_descriptor_validated": len(validation_errors) == 0,
            "next_required_artifact": "replace qualitative descriptors with computed structural/electronic descriptors and B5-linked observables",
        },
    }


def markdown_report(payload: dict) -> str:
    metrics = payload["metrics"]
    top_rows_md = "\n".join(
        f"| {row['rank']} | {row['formula']} | {row['family']} | {row['discovery_year']} | "
        f"{row['tc_k']:.1f} | {row['pressure_gpa']:.1f} | {row['physics_descriptor_score']:.4f} |"
        for row in payload["top_physics_rows"]
    )
    post_rows_md = "\n".join(
        f"| {row['rank']} | {row['formula']} | {row['family']} | {row['discovery_year']} | "
        f"{row['tc_k']:.1f} | {row['pressure_gpa']:.1f} | {row['physics_descriptor_score']:.4f} |"
        for row in payload["top_post_split_physics_rows"]
    )
    errors = payload["validation_errors"] or ["none"]
    error_lines = "\n".join(f"- {item}" for item in errors)
    return f"""# B6 Curated Materials Leakage Audit v0

Status: `{payload['status']}`

This artifact upgrades B6 from a synthetic descriptor toy to a small curated
retrospective table with explicit time-split and family-prior leakage pressure.
It is not a material-discovery claim, not a solved high-Tc mechanism, and not a
complete superconductivity database.

## Dataset

- Records: {payload['record_count']}
- Families: {payload['family_count']}
- Split year: {payload['split_year']}
- Post-split records: {payload['post_split_record_count']}
- High-Tc threshold: {payload['high_tc_threshold_k']} K
- Source scope: {payload['source_scope']}

## Leakage Metrics

| Metric | Value |
|---|---:|
| All physics precision@{payload['top_k']} | {metrics['all_physics_precision_at_k']:.6f} |
| All physics average precision@{payload['top_k']} | {metrics['all_physics_average_precision_at_k']:.6f} |
| All random average precision@{payload['top_k']} mean | {metrics['all_random_average_precision_at_k_mean']:.6f} |
| Post-split physics average precision | {metrics['post_split_physics_average_precision_at_k']:.6f} |
| Post-split family-prior average precision | {metrics['post_split_family_prior_average_precision_at_k']:.6f} |
| Post-split leaky combined average precision | {metrics['post_split_leaky_family_combined_average_precision_at_k']:.6f} |
| Leaky combined minus physics AP | {metrics['leaky_family_combined_minus_physics_ap']:.6f} |
| Family-holdout mean physics AP | {metrics['family_holdout_mean_physics_ap']:.6f} |
| Family-holdout mean random AP | {metrics['family_holdout_mean_random_ap']:.6f} |

## Top Physics-Descriptor Rows

| Rank | Formula | Family | Year | Tc K | Pressure GPa | Score |
|---:|---|---|---:|---:|---:|---:|
{top_rows_md}

## Post-Split Top Rows

| Rank | Formula | Family | Year | Tc K | Pressure GPa | Score |
|---:|---|---|---:|---:|---:|---:|
{post_rows_md}

## Validation Errors

{error_lines}

## Interpretation

- The table is now real/curated enough to expose family and time leakage, but it
  is still much too small for material discovery.
- The descriptor ranking is evaluated against a family-prior baseline and a
  leaky family-combined score, so future B6 claims cannot hide behind family
  labels.
- The next B6 artifact must replace qualitative descriptor values with computed
  structural, electronic, and B5-linked observables.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--split-year", type=int, default=2008)
    parser.add_argument("--high-tc-threshold-k", type=float, default=30.0)
    parser.add_argument("--seed", type=int, default=61037)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    payload = run(
        top_k=args.top_k,
        split_year=args.split_year,
        threshold=args.high_tc_threshold_k,
        seed=args.seed,
    )
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(
        json.dumps(payload, indent=2 if args.pretty else None, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_output.write_text(markdown_report(payload), encoding="utf-8")
    print(json.dumps(payload, indent=2 if args.pretty else None, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
