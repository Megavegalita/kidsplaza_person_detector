#!/usr/bin/env python3
"""
Shared utilities for mapping classifier logits to gender labels consistently.

Conventions supported:
- male0_female1: index 0 => 'M', index 1 => 'F'
- female0_male1: index 0 => 'F', index 1 => 'M'
"""

from typing import Optional, Tuple


def map_logits_to_gender(
    prob_class0: float,
    prob_class1: float,
    convention: str,
    *,
    min_confidence: Optional[float] = None,
    female_min_confidence: Optional[float] = None,
    male_min_confidence: Optional[float] = None,
) -> Tuple[str, float]:
    """Map two-class probabilities to ('M'|'F', confidence) using a convention.

    Args:
        prob_class0: Probability of class index 0.
        prob_class1: Probability of class index 1.
        convention: Either 'male0_female1' or 'female0_male1'.

    Returns:
        Tuple of (gender_label, confidence). If below threshold, returns ("Unknown", confidence).

    Raises:
        ValueError: If convention is unsupported.
    """
    if convention not in ("male0_female1", "female0_male1"):
        raise ValueError(f"Unsupported convention: {convention}")

    if prob_class0 >= prob_class1:
        idx = 0
        conf = float(prob_class0)
    else:
        idx = 1
        conf = float(prob_class1)

    if convention == "male0_female1":
        label = "M" if idx == 0 else "F"
    else:
        label = "F" if idx == 0 else "M"

    # Apply optional asymmetric thresholds
    if label == "F":
        thr = (
            female_min_confidence
            if female_min_confidence is not None
            else min_confidence
        )
    elif label == "M":
        thr = male_min_confidence if male_min_confidence is not None else min_confidence
    else:
        thr = min_confidence

    if thr is not None and conf < float(thr):
        return "Unknown", conf

    return label, conf
