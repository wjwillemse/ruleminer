"""Pandas parser module."""

import re
import pandas as pd
from typing import Dict

from .const import DUNDER_DF


def dataframe_lengths(
    expression: str,
    required: list,
    data: pd.DataFrame,
) -> Dict[str, str]:
    """
    Calculate lengths based on an rule expression and generate corresponding values.

    This function takes a rule expression, such as 'if A then B', and a list
    of required variables ('N', 'X', 'Y', '~X', '~Y', 'X and Y', 'X and ~Y',
    '~X and ~Y'). It calculates lengths or sums of data based on the given
    conditional expression for each required variable.

    Args:
        expression (str): A conditional expression in the format 'if A then B'.
        required (List[str]): A list of required variables for which to calculate
        lengths or sums.

    Returns:
        Dict[str, str]: A dictionary where keys are required variable names, and
        values are corresponding length or sum calculations.

    Example:
        >>> expression = "if ({"A"} > 0) then ({"B"} < 10)"
        >>> required = ['X', 'Y', 'X and Y']
        >>> result = ruleminer.dataframe_lengths(expression, required)
        >>> print(result)
        {'X': '((__df__["A"] > 0)).sum()', 'Y': '((__df__["B"] < 10)).sum()',
        'X and Y': '(((__df__["A"] > 0)) & ((__df__["B"] < 10))).sum()'}
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
                expressions[variable] = "(" + pandas_column(if_part, data) + ").sum()"
        elif variable == "~X":
            expressions[variable] = "(~(" + pandas_column(if_part, data) + ")).sum()"
        elif variable == "Y":
            expressions[variable] = "(" + pandas_column(then_part, data) + ").sum()"
        elif variable == "~Y":
            expressions[variable] = "(~(" + pandas_column(then_part, data) + ")).sum()"
        elif variable == "X and Y":
            expressions[variable] = (
                "(("
                + pandas_column(if_part, data)
                + ") & ("
                + pandas_column(then_part, data)
                + ")).sum()"
            )
        elif variable == "X and ~Y":
            expressions[variable] = (
                "(("
                + pandas_column(if_part, data)
                + ") & ~("
                + pandas_column(then_part, data)
                + ")).sum()"
            )
        elif variable == "~X and ~Y":
            expressions[variable] = (
                "(~("
                + pandas_column(if_part, data)
                + ") & ~("
                + pandas_column(then_part, data)
                + ")).sum()"
            )

    for e in expressions.keys():
        expressions[e] = expressions[e].replace("[(())]", "")
        expressions[e] = expressions[e].replace("(()) & ", "")
        expressions[e] = expressions[e].replace("[~(())]", "[False]")
    return expressions


def dataframe_index(
    expression: str,
    required: list,
    data: pd.DataFrame,
) -> Dict[str, str]:
    """
    Parse a rule expression and generate corresponding DataFrame index expressions.

    This function takes a rule expression, such as 'if A then B', and a list of
    required variables ('N', 'X', 'Y', '~X', '~Y', 'X and Y', 'X and ~Y', '~X and
    ~Y'). It then generates corresponding DataFrame index expressions for each
    required variable based on the given expression.

    Args:
        expression (str): A rule expression in the format 'if A then B'.
        required (List[str]): A list of required variables for which to generate
        index expressions.

    Returns:
        Dict[str, str]: A dictionary where keys are required variable names, and
        values are corresponding DataFrame index expressions.

    Example:
        >>> expression = 'if ({"A"} > 0) then ({"B"} < 10)'
        >>> required = ['X', 'Y', 'X and Y']
        >>> result = ruleminer.dataframe_index(expression, required)
        >>> print(result)
        {
          'X': '__df__.index[((__df__["A"] > 0))]',
          'Y': '__df__.index[((__df__["B"] < 10))]',
          'X and Y': '__df__.index[((__df__["A"] > 0)) & ((__df__["B"] < 10))]'
        }
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
                DUNDER_DF + ".index[(" + pandas_column(if_part, data) + ")]"
            )
        elif variable == "~X":
            expressions[variable] = (
                DUNDER_DF + ".index[~(" + pandas_column(if_part, data) + ")]"
            )
        elif variable == "Y":
            expressions[variable] = (
                DUNDER_DF + ".index[(" + pandas_column(then_part, data) + ")]"
            )
        elif variable == "~Y":
            expressions[variable] = (
                DUNDER_DF + ".index[~(" + pandas_column(then_part, data) + ")]"
            )
        elif variable == "X and Y":
            expressions[variable] = (
                DUNDER_DF
                + ".index[("
                + pandas_column(if_part, data)
                + ") & ("
                + pandas_column(then_part, data)
                + ")]"
            )
        elif variable == "X and ~Y":
            expressions[variable] = (
                DUNDER_DF
                + ".index[("
                + pandas_column(if_part, data)
                + ") & ~("
                + pandas_column(then_part, data)
                + ")]"
            )
        elif variable == "~X and ~Y":
            expressions[variable] = (
                DUNDER_DF
                + ".index[~("
                + pandas_column(if_part, data)
                + ") & ~("
                + pandas_column(then_part, data)
                + ")]"
            )
    for e in expressions.keys():
        expressions[e] = expressions[e].replace("[(())]", "")
        expressions[e] = expressions[e].replace("(()) & ", "")
        expressions[e] = expressions[e].replace("[~(())]", "[False]")
    return expressions


def pandas_column(
    expression: str,
    data: pd.DataFrame,
):
    """
    Replace column names with Pandas DataFrame expressions.

    This function takes a string containing column names enclosed in curly braces,
    e.g., {"A"}, and converts them to Pandas DataFrame syntax, e.g., __df__["A"].

    Args:
        expression (str): A string with column names enclosed in curly
        braces, e.g., {"A"}.

    Returns:
        str: The Pandas DataFrame expression with columns in the
        format __df__["A"].

    Example:
        >>> expression = '{"A"}'
        >>> result = ruleminer.pandas_column(expression)
        >>> print(result)
        "__df__[A]"
    """
    result = ""
    offset = 0
    if expression == "()":
        return expression
    for idx, c in enumerate(expression):
        if c == "{":
            start_column = offset + idx
        elif c == "}":
            end_column = offset + idx
            params = expression[start_column - offset : end_column - offset + 1].rsplit(
                " ", 2
            )
            if len(params) == 3 and params[0][-1] in ['"', "'"]:
                column, direction, key = params
                if (
                    (not pd.api.types.is_string_dtype(data[column[2:-1]]))
                    and (not pd.api.types.is_bool_dtype(data[column[2:-1]]))
                    and (not pd.api.types.is_datetime64_ns_dtype(data[column[2:-1]]))
                ):
                    column_expr = (
                        "("
                        + column
                        + "}"
                        + direction
                        + "0.5*abs("
                        + column
                        + "}"
                        + '.apply(__tol__, args=("'
                        + key[:-1]
                        + '",)'
                        + ")))"
                    )
                    result = result[:start_column] + column_expr
                    offset += len(column_expr) - (end_column - start_column) - 1
                else:
                    result = result[:start_column] + " ".join(params)
            else:
                result = result[:start_column] + " ".join(params)
        else:
            result += c
    return result.replace('{"', DUNDER_DF + '["').replace('"}', '"]')


def dataframe_values(expression: str, data: pd.DataFrame()):
    """
    Extract values from a Pandas DataFrame based on an expression.

    This function constructs a Pandas DataFrame expression to extract
    values based on the provided expression. The expression is wrapped
    in square brackets to retrieve the values from the DataFrame.

    Args:
        expression (str): An expression used to filter or access
        DataFrame values, e.g., "{Column_A > 0}".

    Returns:
        str: The Pandas DataFrame expression to retrieve values based
        on the provided expression.

    Example:
        >>> expression = '{"A"} > 0'
        >>> result = ruleminer.dataframe_values(expression)
        >>> print(result)
        "__df__[(__df__["A"] > 0)]"
    """
    if expression != "":
        expression = "[(" + pandas_column(expression, data) + ")]"
    return DUNDER_DF + expression
