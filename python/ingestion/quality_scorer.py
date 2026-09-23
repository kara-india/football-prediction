"""
Match Data Quality Scorer
Evaluates data completeness, validates temporal and statistical consistency,
and detects data corruption or anomalies in match records.
"""
from typing import Dict, Any, List, Tuple


class MatchQualityScorer:
    """Scores match record completeness and flags statistical anomalies."""

    @staticmethod
    def score_match(record: Dict[str, Any]) -> Tuple[float, List[str]]:
        """Compute data quality score (0.0 to 1.0) and identify any anomalies.

        Args:
            record: Dict containing match stats (home_team, away_team, fthg, ftag,
                    hthg, htag, hs, as_shots, hst, ast, hc, ac, hy, ay, hr, ar,
                    b365_h, b365_d, b365_a).

        Returns:
            Tuple of (quality_score: float, anomalies: List[str])
        """
        anomalies: List[str] = []

        # 1. Critical existence check
        fthg = record.get("fthg")
        ftag = record.get("ftag")

        if fthg is None or ftag is None:
            return 0.0, ["MISSING_FULLTIME_SCORE"]

        # 2. Check for negative numbers
        numeric_fields = [
            ("fthg", fthg), ("ftag", ftag),
            ("hthg", record.get("hthg")), ("htag", record.get("htag")),
            ("hs", record.get("hs")), ("as_shots", record.get("as_shots")),
            ("hst", record.get("hst")), ("ast", record.get("ast")),
            ("hc", record.get("hc")), ("ac", record.get("ac")),
            ("hy", record.get("hy")), ("ay", record.get("ay")),
            ("hr", record.get("hr")), ("ar", record.get("ar")),
        ]

        for name, val in numeric_fields:
            if val is not None and val < 0:
                anomalies.append(f"NEGATIVE_VALUE_{name.upper()}_{val}")

        # 3. Half-time vs Full-time consistency
        hthg = record.get("hthg")
        htag = record.get("htag")
        if hthg is not None and hthg > fthg:
            anomalies.append(f"HALFTIME_EXCEEDS_FULLTIME_HOME ({hthg} > {fthg})")
        if htag is not None and htag > ftag:
            anomalies.append(f"HALFTIME_EXCEEDS_FULLTIME_AWAY ({htag} > {ftag})")

        # 4. Shots vs Shots-on-target consistency
        hs = record.get("hs")
        hst = record.get("hst")
        as_shots = record.get("as_shots")
        ast = record.get("ast")

        if hs is not None and hst is not None and hst > hs:
            anomalies.append(f"SHOTS_ON_TARGET_EXCEEDS_TOTAL_HOME ({hst} > {hs})")
        if as_shots is not None and ast is not None and ast > as_shots:
            anomalies.append(f"SHOTS_ON_TARGET_EXCEEDS_TOTAL_AWAY ({ast} > {as_shots})")

        # 5. Red cards sanity check (max 4 per team before abandonment)
        hr = record.get("hr")
        ar = record.get("ar")
        if hr is not None and hr > 4:
            anomalies.append(f"EXCESSIVE_RED_CARDS_HOME ({hr})")
        if ar is not None and ar > 4:
            anomalies.append(f"EXCESSIVE_RED_CARDS_AWAY ({ar})")

        # 6. Impossible goal-to-shots consistency
        if hs is not None and fthg > hs:
            anomalies.append(f"MORE_GOALS_THAN_SHOTS_HOME ({fthg} > {hs})")
        if as_shots is not None and ftag > as_shots:
            anomalies.append(f"MORE_GOALS_THAN_SHOTS_AWAY ({ftag} > {as_shots})")

        # 7. Compute completeness score
        has_half_scores = hthg is not None and htag is not None
        has_shots = hs is not None and as_shots is not None
        has_corners_cards = (
            record.get("hc") is not None and
            record.get("hy") is not None and
            record.get("ay") is not None
        )
        has_odds = (
            record.get("b365_h") is not None and
            record.get("b365_d") is not None and
            record.get("b365_a") is not None
        )

        score = 0.5  # Base score for valid full-time result
        if has_half_scores:
            score += 0.1
        if has_shots:
            score += 0.15
        if has_corners_cards:
            score += 0.1
        if has_odds:
            score += 0.15

        # Penalize for severe anomalies
        if anomalies:
            score = max(0.1, score - 0.2 * len(anomalies))

        return round(min(1.0, max(0.0, score)), 2), anomalies
