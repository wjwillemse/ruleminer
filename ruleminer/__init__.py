"""Top-level package for ruleminer."""

__author__ = """Willem Jan Willemse"""
__email__ = "w.j.willemse@dnb.nl"

from .ruleminer import (
    rule_expression,
    RuleMiner,
    flatten_and_sort,
    RULE_ID,
    RULE_GROUP,
    RULE_DEF,
    ABSOLUTE_SUPPORT,
    ABSOLUTE_EXCEPTIONS,
    CONFIDENCE,
    NOT_APPLICABLE,
    ENCODINGS,
)
from .grammar import (
    condition_expression,
    math_expression,
    _quoted_string,
    _column,
)
from .parser import (
    RuleParser,
    contains_column,
    contains_string,
)
from .evaluator import CodeEvaluator
from .utils import (
    tree_to_expressions,
    fit_ensemble_and_extract_expressions,
    fit_dataframe_to_ensemble,
)
from .tolerance import FloatWithTolerance

__all__ = [
    RuleMiner,
    RuleParser,
    CodeEvaluator,
    contains_column,
    contains_string,
    rule_expression,
    condition_expression,
    flatten_and_sort,
    RULE_ID,
    RULE_GROUP,
    RULE_DEF,
    ABSOLUTE_SUPPORT,
    ABSOLUTE_EXCEPTIONS,
    CONFIDENCE,
    NOT_APPLICABLE,
    ENCODINGS,
    math_expression,
    _quoted_string,
    _column,
    tree_to_expressions,
    fit_ensemble_and_extract_expressions,
    fit_dataframe_to_ensemble,
    FloatWithTolerance,
]
