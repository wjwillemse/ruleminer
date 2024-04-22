"""Top-level package for ruleminer."""

__author__ = """Willem Jan Willemse"""
__email__ = "w.j.willemse@dnb.nl"
__version__ = "0.1.26"

from .ruleminer import (
    rule_expression,
    RuleMiner,
    RULE_ID,
    RULE_GROUP,
    RULE_DEF,
    RULE_STATUS,
    ABSOLUTE_SUPPORT,
    ABSOLUTE_EXCEPTIONS,
    CONFIDENCE,
    ENCODINGS,
    flatten_and_sort,
)
from .parser import (
    math_expression,
    function_expression,
    _quoted_string,
    _column,
)

from .utils import(
    tree_to_expressions,
    fit_ensemble_and_extract_expressions,
    fit_dataframe_to_ensemble,
)