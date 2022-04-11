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
    SUPPORT: ["X", "~X"],
    ADDED_VALUE: ["X", "~X", "X and Y"],  # conf(X⇒Y) − supp(Y)
    CASUAL_CONFIDENCE: ["X", "X and Y", "~X", "~X and ~Y"],
    CONVICTION: ["X", "Y", "~Y", "X and Y"],
    LIFT: ["X", "Y", "~Y", "X and Y"],
    RULE_POWER_FACTOR: ["X", "Y", "~Y", "X and Y"],
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


def calculate_metrics(results: dict = {}, metrics: list = []):
    """ """
    calculated_metrics = {}
    for metric in metrics:
        if metric == ABSOLUTE_SUPPORT:
            if results["X and Y"] is not None:
                calculated_metrics[metric] = len(results["X and Y"])
            else:
                calculated_metrics[metric] = np.nan
        elif metric == ABSOLUTE_EXCEPTIONS:
            if results["X and ~Y"] is not None:
                calculated_metrics[metric] = len(results["X and ~Y"])
            else:
                calculated_metrics[metric] = np.nan
        elif metric == CONFIDENCE:
            if results["X"] is not None and results["X and Y"] is not None:
                if len(results["X"]) != 0:
                    calculated_metrics[metric] = len(results["X and Y"]) / len(
                        results["X"]
                    )
                else:
                    calculated_metrics[metric] = np.nan
            else:
                calculated_metrics[metric] = np.nan
        elif metric == SUPPORT:
            if results["X"] is not None and results["~X"] is not None:
                if len(results["X"]) + len(results["~X"]) != 0:
                    calculated_metrics[metric] = len(results["X"]) / (
                        len(results["X"]) + len(results["~X"])
                    )
                else:
                    calculated_metrics[metric] = np.nan
            else:
                calculated_metrics[metric] = np.nan
        elif metric == ADDED_VALUE:
            if (
                results["X"] is not None
                and results["X and Y"] is not None
                and results["~X"] is not None
            ):
                if (
                    len(results["X"]) != 0
                ):
                    calculated_metrics[metric] = len(results["X and Y"]) / len(
                        results["X"]
                    )
                    calculated_metrics[metric] -= len(results["X"]) / (
                        len(results["X"]) + len(results["~X"])
                    )
                else:
                    calculated_metrics[metric] = np.nan
            else:
                calculated_metrics[metric] = np.nan
        elif metric == CASUAL_CONFIDENCE:
            if (
                results["X"] is not None
                and results["X and Y"] is not None
                and results["~X"] is not None
                and results["~X and ~Y"] is not None
            ):
                if len(results["X"]) != 0 and len(results["~X"]) != 0:
                    calculated_metrics[metric] = (
                        0.5 * len(results["X and Y"]) / len(results["X"])
                    )
                    calculated_metrics[metric] += (
                        0.5 * len(results["~X and ~Y"]) / len(results["~X"])
                    )
                else:
                    calculated_metrics[metric] = np.nan
            else:
                calculated_metrics[metric] = np.nan
        elif metric == CONVICTION:
            if (
                results["X"] is not None
                and results["X and Y"] is not None
                and results["Y"] is not None
                and results["~Y"] is not None
            ):
                if (
                    len(results["X"]) != 0
                    and (len(results["Y"]) + len(results["~Y"])) != 0
                    and (1 - len(results["X and Y"]) / len(results["X"])) != 0
                ):
                    calculated_metrics[metric] = 1 - len(results["Y"]) / (
                        len(results["Y"]) + len(results["~Y"])
                    )
                    calculated_metrics[metric] /= 1 - len(results["X and Y"]) / len(
                        results["X"]
                    )
                else:
                    calculated_metrics[metric] = np.nan
            else:
                calculated_metrics[metric] = np.nan
        elif metric == LIFT:
            if (
                results["X"] is not None
                and results["X and Y"] is not None
                and results["Y"] is not None
                and results["~Y"] is not None
            ):
                if (
                    len(results["X"]) != 0
                    and (len(results["Y"]) + len(results["~Y"])) != 0
                    and (len(results["Y"]) / (len(results["Y"]) + len(results["~Y"])))
                    != 0
                ):
                    calculated_metrics[metric] = len(results["X and Y"]) / len(
                        results["X"]
                    )
                    calculated_metrics[metric] /= len(results["Y"]) / (
                        len(results["Y"]) + len(results["~Y"])
                    )
                else:
                    calculated_metrics[metric] = np.nan
            else:
                calculated_metrics[metric] = np.nan
        elif metric == RULE_POWER_FACTOR:
            if (
                results["X"] is not None
                and results["Y"] is not None
                and results["X and Y"] is not None
            ):
                if (
                    len(results["X"]) != 0
                    and len(results["Y"]) + len(results["~Y"]) != 0
                ):
                    calculated_metrics[metric] = (
                        len(results["Y"])
                        / (len(results["Y"]) + len(results["~Y"]))
                        * len(results["X and Y"])
                        / len(results["X"])
                    )
                else:
                    calculated_metrics[metric] = np.nan
            else:
                calculated_metrics[metric] = np.nan

    return calculated_metrics
