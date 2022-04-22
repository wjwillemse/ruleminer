"""Metrics module."""

from ruleminer.const import ABSOLUTE_SUPPORT
from ruleminer.const import ABSOLUTE_EXCEPTIONS
from ruleminer.const import SUPPORT
from ruleminer.const import CONFIDENCE
from ruleminer.const import ADDED_VALUE
from ruleminer.const import CASUAL_CONFIDENCE
from ruleminer.const import CASUAL_SUPPORT
from ruleminer.const import LIFT
from ruleminer.const import CONVICTION
from ruleminer.const import RULE_POWER_FACTOR

import numpy as np

METRICS = {
    ABSOLUTE_SUPPORT: ["X and Y"],
    ABSOLUTE_EXCEPTIONS: ["X and ~Y"],
    CONFIDENCE: ["X", "X and Y"],
    SUPPORT: ["N", "X and Y"],
    ADDED_VALUE: ["N", "X", "Y", "X and Y"],
    CASUAL_CONFIDENCE: ["X", "~X", "X and Y", "~X and ~Y"],
    CONVICTION: ["N", "X", "Y", "X and Y"],
    LIFT: ["N", "X", "Y", "X and Y"],
    RULE_POWER_FACTOR: ["N", "X", "X and Y"],
}


def required_variables(metrics: list = []):
    """
    This function derives a set of variables that are needed to calculate the metrics
    """
    variables = set()
    for metric in metrics:
        required = METRICS.get(metric, [])
        for v in required:
            variables.add(v)
    return variables


def metrics(metrics: list = []):
    return [metric for metric in metrics if metric in METRICS.keys()]


def calculate_metrics(len_results: dict = {}, metrics: list = []):
    """ """
    calculated_metrics = {}
    for metric in metrics:
        if metric == ABSOLUTE_SUPPORT:
            # n(X and Y)
            calculated_metrics[metric] = len_results.get("X and Y", np.nan)
        elif metric == ABSOLUTE_EXCEPTIONS:
            # n(X and ~Y)
            calculated_metrics[metric] = len_results.get("X and ~Y", np.nan)
        elif metric == CONFIDENCE:
            # conf(X->Y) = n(X and Y) / n(X)
            if len_results.get("X", np.nan) != 0:
                calculated_metrics[metric] = len_results.get(
                    "X and Y", np.nan
                ) / len_results.get("X", np.nan)
            else:
                calculated_metrics[metric] = np.nan
        elif metric == SUPPORT:
            # n(X) / n
            if len_results.get("N", np.nan) != 0:
                calculated_metrics[metric] = len_results.get("X and Y", np.nan) / (
                    len_results.get("N", np.nan)
                )
            else:
                calculated_metrics[metric] = np.nan
        elif metric == ADDED_VALUE:
            # conf(X->Y) - supp(Y)
            if len_results.get("X", np.nan) != 0:
                calculated_metrics[metric] = len_results.get(
                    "X and Y", np.nan
                ) / len_results.get("X", np.nan)
            else:
                calculated_metrics[metric] = np.nan
            if len_results.get("N", np.nan) != 0:
                calculated_metrics[metric] -= len_results.get("Y", np.nan) / (
                    len_results.get("N", np.nan)
                )
            else:
                calculated_metrics[metric] = np.nan
        elif metric == CASUAL_CONFIDENCE:
            # 0.5 * conf(X->Y) + 0.5 * conf(~X->~Y)
            if len_results.get("X", np.nan) != 0:
                calculated_metrics[metric] = (
                    0.5
                    * len_results.get("X and Y", np.nan)
                    / len_results.get("X", np.nan)
                )
            else:
                calculated_metrics[metric] = np.nan
            if len_results.get("~X", np.nan) != 0:
                calculated_metrics[metric] += (
                    0.5
                    * len_results.get("~X and ~Y", np.nan)
                    / len_results.get("~X", np.nan)
                )
            else:
                calculated_metrics[metric] = np.nan
        elif metric == CONVICTION:
            # (1-supp(Y)) / (1-conf(X->Y))
            if len_results.get("N", np.nan) != 0:
                calculated_metrics[metric] = 1 - (
                    len_results.get("Y", np.nan) / len_results.get("N", np.nan)
                )
            else:
                calculated_metrics[metric] = np.nan
            if len_results.get("X", np.nan) != 0:
                calculated_metrics[metric] /= 1 - len_results.get(
                    "X and Y", np.nan
                ) / len_results.get("X", np.nan)
            else:
                calculated_metrics[metric] = np.nan
        elif metric == LIFT:
            # conf(X->Y) / supp(Y)
            if len_results.get("X", np.nan) != 0:
                calculated_metrics[metric] = len_results.get(
                    "X and Y", np.nan
                ) / len_results.get("X", np.nan)
            else:
                calculated_metrics[metric] = np.nan
            if (len_results.get("N", np.nan) != 0) and (
                len_results.get("Y", np.nan) != 0
            ):
                calculated_metrics[metric] /= len_results.get(
                    "Y", np.nan
                ) / len_results.get("N", np.nan)
            else:
                calculated_metrics[metric] = np.nan
        elif metric == RULE_POWER_FACTOR:
            # supp(X->Y) * conf(X->Y)
            if len_results.get("N", np.nan) != 0:
                calculated_metrics[metric] = len_results.get(
                    "X and Y", np.nan
                ) / len_results.get("N", np.nan)
            else:
                calculated_metrics[metric] = np.nan
            if len_results.get("X", np.nan) != 0:
                calculated_metrics[metric] *= len_results.get(
                    "X and Y", np.nan
                ) / len_results.get("X", np.nan)
            else:
                calculated_metrics[metric] = np.nan
    return calculated_metrics
