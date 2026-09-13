import math
from typing import List, Dict, Any, Tuple, Optional

class OutlierDetectionMethod:
    IQR = "IQR"
    MAD = "MAD"
    ROBUST_ZSCORE = "ROBUST_ZSCORE"
    ROUTE_HISTORY_THRESHOLD = "ROUTE_HISTORY_THRESHOLD"

def detect_outliers_iqr(prices: List[float], k: float = 1.5) -> List[bool]:
    """
    Interquartile Range (IQR) outlier detection method.
    Flagged if price < Q1 - k*IQR or price > Q3 + k*IQR.
    """
    if len(prices) < 4:
        return [False] * len(prices)

    sorted_p = sorted(prices)
    n = len(sorted_p)
    q1 = sorted_p[n // 4]
    q3 = sorted_p[(3 * n) // 4]
    iqr = q3 - q1

    if iqr == 0:
        return [False] * len(prices)

    lower_bound = q1 - k * iqr
    upper_bound = q3 + k * iqr

    return [p < lower_bound or p > upper_bound for p in prices]

def detect_outliers_mad(prices: List[float], threshold: float = 3.0) -> List[bool]:
    """
    Median Absolute Deviation (MAD) outlier detection method.
    MAD = median(|p - median(p)|).
    """
    if len(prices) < 3:
        return [False] * len(prices)

    sorted_p = sorted(prices)
    median_p = sorted_p[len(sorted_p) // 2]
    deviations = [abs(p - median_p) for p in prices]
    sorted_dev = sorted(deviations)
    mad = sorted_dev[len(sorted_dev) // 2]

    if mad == 0:
        return [False] * len(prices)

    return [(abs(p - median_p) / mad) > threshold for p in prices]

def detect_outliers_robust_zscore(prices: List[float], threshold: float = 3.5) -> List[bool]:
    """
    Robust Z-Score detection method using Median and MAD.
    Modified Z = 0.6745 * |p - median| / MAD.
    """
    if len(prices) < 3:
        return [False] * len(prices)

    sorted_p = sorted(prices)
    median_p = sorted_p[len(sorted_p) // 2]
    deviations = [abs(p - median_p) for p in prices]
    sorted_dev = sorted(deviations)
    mad = sorted_dev[len(sorted_dev) // 2]

    if mad == 0:
        return [False] * len(prices)

    return [(0.6745 * abs(p - median_p) / mad) > threshold for p in prices]

def detect_outliers_route_history(
    prices: List[float], historical_median: float, max_deviation_pct: float = 0.5
) -> List[bool]:
    """
    Route-history threshold outlier detection method.
    Flagged if price deviates by more than max_deviation_pct from historical median.
    """
    if historical_median <= 0:
        return [False] * len(prices)

    return [abs(p - historical_median) / historical_median > max_deviation_pct for p in prices]

def flag_anomalies(
    prices: List[float],
    method: str = OutlierDetectionMethod.IQR,
    historical_median: Optional[float] = None,
    **kwargs
) -> List[bool]:
    """
    Flags anomalies across input prices using the requested versioned method.
    NOTE: Flagging does NOT automatically exclude observations.
    """
    if not prices:
        return []

    if method == OutlierDetectionMethod.IQR:
        k = kwargs.get("k", 1.5)
        return detect_outliers_iqr(prices, k=k)
    elif method == OutlierDetectionMethod.MAD:
        threshold = kwargs.get("threshold", 3.0)
        return detect_outliers_mad(prices, threshold=threshold)
    elif method == OutlierDetectionMethod.ROBUST_ZSCORE:
        threshold = kwargs.get("threshold", 3.5)
        return detect_outliers_robust_zscore(prices, threshold=threshold)
    elif method == OutlierDetectionMethod.ROUTE_HISTORY_THRESHOLD:
        h_med = historical_median or (sum(prices) / len(prices))
        max_dev = kwargs.get("max_deviation_pct", 0.5)
        return detect_outliers_route_history(prices, historical_median=h_med, max_deviation_pct=max_dev)
    else:
        # Default fallback to IQR
        return detect_outliers_iqr(prices)

def filter_eligible_observations(
    observations: List[Dict[str, Any]],
    apply_exclusion: bool = True,
    method: str = OutlierDetectionMethod.IQR
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Explicitly separates eligible vs excluded observations.
    Demonstrates flagging vs exclusion policy separation.
    """
    if not observations:
        return [], []

    prices = [float(obs.get("price") or obs.get("total_fare") or 0.0) for obs in observations]
    flagged_mask = flag_anomalies(prices, method=method)

    eligible = []
    excluded = []

    for obs, is_flagged in zip(observations, flagged_mask):
        obs_copy = dict(obs)
        obs_copy["is_anomalous"] = is_flagged
        
        if apply_exclusion and is_flagged:
            obs_copy["exclusion_reason"] = f"EXCLUDED_BY_{method}_OUTLIER_POLICY"
            excluded.append(obs_copy)
        else:
            eligible.append(obs_copy)

    return eligible, excluded
