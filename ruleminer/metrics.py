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
from ruleminer.const import VAR_X
from ruleminer.const import VAR_NOT_X
from ruleminer.const import VAR_Y
from ruleminer.const import VAR_Z
from ruleminer.const import VAR_N
from ruleminer.const import VAR_NOT_Y
from ruleminer.const import VAR_X_AND_Y
from ruleminer.const import VAR_X_AND_NOT_Y
from ruleminer.const import VAR_NOT_X_AND_NOT_Y

import numpy as np

METRICS = {
    ABSOLUTE_SUPPORT: [VAR_X_AND_Y],
    ABSOLUTE_EXCEPTIONS: [VAR_X_AND_NOT_Y],
    CONFIDENCE: [VAR_X, VAR_X_AND_Y],
    SUPPORT: [VAR_N, VAR_X_AND_Y],
    ADDED_VALUE: [VAR_N, VAR_X, VAR_Y, VAR_X_AND_Y],
    CASUAL_CONFIDENCE: [VAR_X, VAR_NOT_X, VAR_X_AND_Y, VAR_NOT_X_AND_NOT_Y],
    CONVICTION: [VAR_N, VAR_X, VAR_Y, VAR_X_AND_Y],
    LIFT: [VAR_N, VAR_X, VAR_Y, VAR_X_AND_Y],
    RULE_POWER_FACTOR: [VAR_N, VAR_X, VAR_X_AND_Y],
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
            calculated_metrics[metric] = len_results.get(VAR_X_AND_Y, np.nan)
        elif metric == ABSOLUTE_EXCEPTIONS:
            # n(X and ~Y)
            calculated_metrics[metric] = len_results.get(VAR_X_AND_NOT_Y, np.nan)
        elif metric == CONFIDENCE:
            # conf(X->Y) = n(X and Y) / n(X)
            if len_results.get(VAR_X, np.nan) != 0:
                calculated_metrics[metric] = len_results.get(
                    VAR_X_AND_Y, np.nan
                ) / len_results.get(VAR_X, np.nan)
            else:
                calculated_metrics[metric] = np.nan
        elif metric == SUPPORT:
            # n(X) / n
            if len_results.get(VAR_N, np.nan) != 0:
                calculated_metrics[metric] = len_results.get(VAR_X_AND_Y, np.nan) / (
                    len_results.get(VAR_N, np.nan)
                )
            else:
                calculated_metrics[metric] = np.nan
        elif metric == ADDED_VALUE:
            # conf(X->Y) - supp(Y)
            if len_results.get(VAR_X, np.nan) != 0:
                calculated_metrics[metric] = len_results.get(
                    VAR_X_AND_Y, np.nan
                ) / len_results.get(VAR_X, np.nan)
            else:
                calculated_metrics[metric] = np.nan
            if len_results.get(VAR_N, np.nan) != 0:
                calculated_metrics[metric] -= len_results.get(VAR_Y, np.nan) / (
                    len_results.get(VAR_N, np.nan)
                )
            else:
                calculated_metrics[metric] = np.nan
        elif metric == CASUAL_CONFIDENCE:
            # 0.5 * conf(X->Y) + 0.5 * conf(~X->~Y)
            if len_results.get(VAR_X, np.nan) != 0:
                calculated_metrics[metric] = (
                    0.5
                    * len_results.get(VAR_X_AND_Y, np.nan)
                    / len_results.get(VAR_X, np.nan)
                )
            else:
                calculated_metrics[metric] = np.nan
            if len_results.get(VAR_NOT_X, np.nan) != 0:
                calculated_metrics[metric] += (
                    0.5
                    * len_results.get(VAR_NOT_X_AND_NOT_Y, np.nan)
                    / len_results.get(VAR_NOT_X, np.nan)
                )
            else:
                calculated_metrics[metric] = np.nan
        elif metric == CONVICTION:
            # (1-supp(Y)) / (1-conf(X->Y))
            if len_results.get(VAR_N, np.nan) != 0:
                calculated_metrics[metric] = 1 - (
                    len_results.get(VAR_Y, np.nan) / len_results.get(VAR_N, np.nan)
                )
            else:
                calculated_metrics[metric] = np.nan
            if len_results.get(VAR_X, np.nan) != 0:
                calculated_metrics[metric] /= 1 - len_results.get(
                    VAR_X_AND_Y, np.nan
                ) / len_results.get(VAR_X, np.nan)
            else:
                calculated_metrics[metric] = np.nan
        elif metric == LIFT:
            # conf(X->Y) / supp(Y)
            if len_results.get(VAR_X, np.nan) != 0:
                calculated_metrics[metric] = len_results.get(
                    VAR_X_AND_Y, np.nan
                ) / len_results.get(VAR_X, np.nan)
            else:
                calculated_metrics[metric] = np.nan
            if (len_results.get(VAR_N, np.nan) != 0) and (
                len_results.get(VAR_Y, np.nan) != 0
            ):
                calculated_metrics[metric] /= len_results.get(
                    VAR_Y, np.nan
                ) / len_results.get(VAR_N, np.nan)
            else:
                calculated_metrics[metric] = np.nan
        elif metric == RULE_POWER_FACTOR:
            # supp(X->Y) * conf(X->Y)
            if len_results.get(VAR_N, np.nan) != 0:
                calculated_metrics[metric] = len_results.get(
                    VAR_X_AND_Y, np.nan
                ) / len_results.get(VAR_N, np.nan)
            else:
                calculated_metrics[metric] = np.nan
            if len_results.get(VAR_X, np.nan) != 0:
                calculated_metrics[metric] *= len_results.get(
                    VAR_X_AND_Y, np.nan
                ) / len_results.get(VAR_X, np.nan)
            else:
                calculated_metrics[metric] = np.nan
    return calculated_metrics
