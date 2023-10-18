"""Parser module."""

import pandas as pd
import logging
import itertools
import re
import pyparsing
from pyparsing import *
from typing import Dict

from ruleminer.const import DUNDER_DF
from ruleminer.const import VAR_Z

lpar, rpar = map(Suppress, "()")
number = Regex(r"[+-]?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?")
function = one_of(
    "min max abs quantile sum substr split count sumif countif MIN MAX ABS QUANTILE SUM SUBSTR SPLIT COUNT SUMIF COUNTIF"
)
empty = one_of(["None", '""', "pd.NA", "np.nan"])
quote = Literal('"')
sep = Literal(",")
string = (
    srange(r"[a-zA-Z0-9_.,:;<>*=+-/?|@#$%^&\[\]{}\(\)\\']")
    + " "
    + "\x01"
    + "\x02"
    + "\x03"
    + pyparsing.pyparsing_unicode.Greek.alphas
    + pyparsing.pyparsing_unicode.Greek.alphanums
)
quoted_string = Combine(quote + Word(string) + quote)
column = Combine("{" + quote + Word(string) + quote + "}")
addop = Literal("+") | Literal("-")
multop = Literal("*") | Literal("/")
expop = Literal("**")
compa_op = one_of(">= > <= < != == in IN")

list_element = quoted_string | column | number | empty
quoted_string_list = Group(
    Literal("[") + list_element + (sep + list_element)[0, ...] + Literal("]")
) | Group(
    lpar
    + Literal("[")
    + list_element
    + (sep + list_element)[0, ...]
    + Literal("]")
    + rpar
)


def function_expression():
    """
    Define a ruleminer function expression

    This function defines a function expression. It uses pyparsing to define 
    the syntax for function calls with parameters, including basic mathematical 
    operations and comparisons.

    Returns:
        pyparsing.core.Forward: a function expression

    Example:
        >>> expression = 'substr({"A"}, 1, 1)'
        >>> result = ruleminer.function_expression().parse_string(expression)
        >>> print(result)
        ['substr', ['{"A"}', ',', '1', ',', '1']]
    """
    expr = Forward()
    params = Forward()
    math_expr = math_expression(expr)
    param_element = (
        math_expr | quoted_string_list | quoted_string | column | number | empty
    )
    param_condition = param_element + compa_op + param_element
    param = param_condition | param_element
    params <<= param + (sep + param)[...]
    expr <<= function + Group(lpar + params + rpar)
    return expr


def math_expression(base: pyparsing.core.Forward = None):
    """
    Define a ruleminer mathematical expression

    This function defines a mathematical expression. It uses pyparsing to define 
    the syntax for function calls with parameters, including basic mathematical 
    operations and comparisons.

    Args:
        None

    Returns:
        pyparsing.core.Forward: a mathematical expression

    Example:
        >>> expression = '{"A"} > 0'
        >>> result = ruleminer.math_expression().parse_string(expression)
        >>> print(result)
        [['{"A"}', '+', '{"B"}']]

    """
    expr = Forward()
    if base is None:
        element = quoted_string_list | quoted_string | column | number | empty
    else:
        element = base | quoted_string_list | quoted_string | column | number | empty
    atom = addop[...] + (element | Group(lpar + expr + rpar))
    factor = Forward()
    factor <<= atom + (expop + factor)[...]
    term = factor + (multop + factor)[...]
    expr <<= term + (addop + term)[...]
    return expr


def rule_expression():
    """
    Define a ruleminer rule expression

    This function defines a ruleminer rule expression. It uses pyparsing to define 
    the syntax for conditions and rule syntax

    Args:
        None

    Returns:
        pyparsing.core.Forward: a ruleminer rule expression

    Example:
        >>> expression = 'if ({"A"} > 0) then ({"B"} < 0)'
        >>> result = ruleminer.rule_expression().parse_string(expression)
        >>> print(result)
        ['if', ['{"A"}', '>', '0'], 'then', ['{"B"}', '<', '0']]
    """
    condition_item = (
        math_expression(function_expression())
        + compa_op
        + math_expression(function_expression())
    )
    comp_expr = Group(lpar + condition_item + rpar)
    condition = infixNotation(
        comp_expr,
        [
            (
                one_of(["NOT", "not", "~"]),
                1,
                opAssoc.RIGHT,
            ),
            (
                one_of(["AND", "and", "&"]),
                2,
                opAssoc.LEFT,
            ),
            (
                one_of(["OR", "or", "|"]),
                2,
                opAssoc.LEFT,
            ),
        ],
    )
    if_then = (
        "if" + condition + "then" + condition | "IF" + condition + "THEN" + condition
    )
    rule_syntax = (
        if_then | "if () then " + condition | "IF () THEN " + condition | condition
    )
    return rule_syntax


def dataframe_lengths(expression: str = "", required: list = []) -> Dict[str, str]:
    """
    Calculate lengths based on an rule expression and generate corresponding values.

    This function takes a rule expression, such as 'if A then B', and a list of required
    variables ('N', 'X', 'Y', '~X', '~Y', 'X and Y', 'X and ~Y', '~X and ~Y'). It calculates
    lengths or sums of data based on the given conditional expression for each required variable.

    Args:
        expression (str): A conditional expression in the format 'if A then B'.
        required (List[str]): A list of required variables for which to calculate lengths or sums.

    Returns:
        Dict[str, str]: A dictionary where keys are required variable names, and values are
        corresponding length or sum calculations.

    Example:
        >>> expression = "if ({"A"} > 0) then ({"B"} < 10)"
        >>> required = ['X', 'Y', 'X and Y']
        >>> result = ruleminer.dataframe_lengths(expression, required)
        >>> print(result)
        {'X': '((__df__["A"] > 0)).sum()', 'Y': '((__df__["B"] < 10)).sum()', 'X and Y': '(((__df__["A"] > 0)) & ((__df__["B"] < 10))).sum()'}
    """
    regex_condition = re.compile(r"if(.*)then(.*)", re.IGNORECASE)
    rule = regex_condition.search(expression)

    if_part = rule.group(1).strip()
    then_part = rule.group(2).strip()

    expressions = {}
    for variable in required:
        if variable == "N":
            expressions[variable] = "len(" + DUNDER_DF + ".values)"
        if variable == "X":
            if if_part == "()":
                expressions[variable] = "len(" + DUNDER_DF + ".index)"
            else:
                expressions[variable] = (
                    "(" + pandas_column(if_part) + ").sum()"
                )
        elif variable == "~X":
            expressions[variable] = "(~(" + pandas_column(if_part) + ")).sum()"
        elif variable == "Y":
            expressions[variable] = "(" + pandas_column(then_part) + ").sum()"
        elif variable == "~Y":
            expressions[variable] = (
                "(~(" + pandas_column(then_part) + ")).sum()"
            )
        elif variable == "X and Y":
            expressions[variable] = (
                "(("
                + pandas_column(if_part)
                + ") & ("
                + pandas_column(then_part)
                + ")).sum()"
            )
        elif variable == "X and ~Y":
            expressions[variable] = (
                "(("
                + pandas_column(if_part)
                + ") & ~("
                + pandas_column(then_part)
                + ")).sum()"
            )
        elif variable == "~X and ~Y":
            expressions[variable] = (
                "(~("
                + pandas_column(if_part)
                + ") & ~("
                + pandas_column(then_part)
                + ")).sum()"
            )

    for e in expressions.keys():
        expressions[e] = expressions[e].replace("[(())]", "")
        expressions[e] = expressions[e].replace("(()) & ", "")
        expressions[e] = expressions[e].replace("[~(())]", "[False]")
    return expressions


def dataframe_index(expression: str = "", required: list = []) -> Dict[str, str]:
    """
    Parse a rule expression and generate corresponding DataFrame index expressions.

    This function takes a rule expression, such as 'if A then B', and a list of required
    variables ('N', 'X', 'Y', '~X', '~Y', 'X and Y', 'X and ~Y', '~X and ~Y'). It then 
    generates corresponding DataFrame index expressions for each required variable 
    based on the given expression.

    Args:
        expression (str): A rule expression in the format 'if A then B'.
        required (List[str]): A list of required variables for which to generate index expressions.

    Returns:
        Dict[str, str]: A dictionary where keys are required variable names, and values are
        corresponding DataFrame index expressions.

    Example:
        >>> expression = 'if ({"A"} > 0) then ({"B"} < 10)'
        >>> required = ['X', 'Y', 'X and Y']
        >>> result = ruleminer.dataframe_index(expression, required)
        >>> print(result)
        {'X': '__df__.index[((__df__["A"] > 0))]', 'Y': '__df__.index[((__df__["B"] < 10))]', 'X and Y': '__df__.index[((__df__["A"] > 0)) & ((__df__["B"] < 10))]'}
    """
    regex_condition = re.compile(r"if(.*)then(.*)", re.IGNORECASE)
    rule = regex_condition.search(expression)

    if_part = rule.group(1).strip()
    then_part = rule.group(2).strip()

    expressions = {}
    for variable in required:
        if variable == "N":
            expressions[variable] = DUNDER_DF + ".index"
        if variable == "X":
            expressions[variable] = (
                DUNDER_DF + ".index[(" + pandas_column(if_part) + ")]"
            )
        elif variable == "~X":
            expressions[variable] = (
                DUNDER_DF + ".index[~(" + pandas_column(if_part) + ")]"
            )
        elif variable == "Y":
            expressions[variable] = (
                DUNDER_DF + ".index[(" + pandas_column(then_part) + ")]"
            )
        elif variable == "~Y":
            expressions[variable] = (
                DUNDER_DF + ".index[~(" + pandas_column(then_part) + ")]"
            )
        elif variable == "X and Y":
            expressions[variable] = (
                DUNDER_DF
                + ".index[("
                + pandas_column(if_part)
                + ") & ("
                + pandas_column(then_part)
                + ")]"
            )
        elif variable == "X and ~Y":
            expressions[variable] = (
                DUNDER_DF
                + ".index[("
                + pandas_column(if_part)
                + ") & ~("
                + pandas_column(then_part)
                + ")]"
            )
        elif variable == "~X and ~Y":
            expressions[variable] = (
                DUNDER_DF
                + ".index[~("
                + pandas_column(if_part)
                + ") & ~("
                + pandas_column(then_part)
                + ")]"
            )
    for e in expressions.keys():
        expressions[e] = expressions[e].replace("[(())]", "")
        expressions[e] = expressions[e].replace("(()) & ", "")
        expressions[e] = expressions[e].replace("[~(())]", "[False]")
    return expressions


def pandas_column(expression: str = ""):
    """
    Replace column names with Pandas DataFrame expressions.

    This function takes a string containing column names enclosed in curly braces,
    e.g., {"A"}, and converts them to Pandas DataFrame syntax, e.g., __df__["A"].

    Args:
        expression (str): A string with column names enclosed in curly braces, e.g., {"A"}.

    Returns:
        str: The Pandas DataFrame expression with columns in the format __df__["A"].

    Example:
        >>> expression = '{"A"}'
        >>> result = ruleminer.pandas_column(expression)
        >>> print(result)
        "__df__[A]"
    """
    return expression.replace("{", DUNDER_DF + "[").replace("}", "]")


def dataframe_values(expression: str = ""):
    """
    Extract values from a Pandas DataFrame based on an expression.

    This function constructs a Pandas DataFrame expression to extract values based on the provided
    expression. The expression is wrapped in square brackets to retrieve the values from the DataFrame.

    Args:
        expression (str): An expression used to filter or access DataFrame values, e.g., "{Column_A > 0}".

    Returns:
        str: The Pandas DataFrame expression to retrieve values based on the provided expression.

    Example:
        >>> expression = '{"A"} > 0'
        >>> result = ruleminer.dataframe_values(expression)
        >>> print(result)
        "__df__[(__df__["A"] > 0)]"
    """
    if expression != "":
        expression = "[(" + pandas_column(expression) + ")]"
    return DUNDER_DF + expression
