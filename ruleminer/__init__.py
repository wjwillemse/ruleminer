"""Top-level package for ruleminer."""

__author__ = """Willem Jan Willemse"""
__email__ = "w.j.willemse@dnb.nl"
__version__ = "0.1.24"

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
