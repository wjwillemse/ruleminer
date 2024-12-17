"""Pandas parser module."""

import re
import pandas as pd
from typing import Dict

from .const import DUNDER_DF
from .const import VAR_X
from .const import VAR_NOT_X
from .const import VAR_Y
from .const import VAR_NOT_Y
from .const import VAR_N
from .const import VAR_X_AND_Y
from .const import VAR_X_AND_NOT_Y
from .const import VAR_NOT_X_AND_NOT_Y


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
        {'X': '((_df["A"] > 0)).sum()', 'Y': '((_df["B"] < 10)).sum()',
        'X and Y': '(((_df["A"] > 0)) & ((_df["B"] < 10))).sum()'}
    """
    regex_condition = re.compile(r"if(.*)then(.*)", re.IGNORECASE)
    rule = regex_condition.search(expression)

    if_part = rule.group(1).strip()
    then_part = rule.group(2).strip()

    expressions = {}
    for variable in required:
        if variable == VAR_N:
            expressions[variable] = "len(" + DUNDER_DF + ".values)"
        if variable == VAR_X:
            if if_part == "()":
                expressions[variable] = "len(" + DUNDER_DF + ".index)"
            else:
                expressions[variable] = "(" + pandas_column(if_part, data) + ").sum()"
        elif variable == VAR_NOT_X:
            expressions[variable] = "(~(" + pandas_column(if_part, data) + ")).sum()"
        elif variable == VAR_Y:
            expressions[variable] = "(" + pandas_column(then_part, data) + ").sum()"
        elif variable == VAR_NOT_Y:
            expressions[variable] = "(~(" + pandas_column(then_part, data) + ")).sum()"
        elif variable == VAR_X_AND_Y:
            expressions[variable] = (
                "(("
                + pandas_column(if_part, data)
                + ") & ("
                + pandas_column(then_part, data)
                + ")).sum()"
            )
        elif variable == VAR_X_AND_NOT_Y:
            expressions[variable] = (
                "(("
                + pandas_column(if_part, data)
                + ") & ~("
                + pandas_column(then_part, data)
                + ")).sum()"
            )
        elif variable == VAR_NOT_X_AND_NOT_Y:
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
          'X': '_df.index[((_df["A"] > 0))]',
          'Y': '_df.index[((_df["B"] < 10))]',
          'X and Y': '_df.index[((_df["A"] > 0)) & ((_df["B"] < 10))]'
        }
    """
    regex_condition = re.compile(r"if(.*)then(.*)", re.IGNORECASE)
    rule = regex_condition.search(expression)

    if_part = rule.group(1).strip()
    then_part = rule.group(2).strip()

    expressions = {}
    for variable in required:
        if variable == VAR_N:
            expressions[variable] = DUNDER_DF + ".index"
        if variable == VAR_X:
            expressions[variable] = (
                DUNDER_DF + ".index[(" + pandas_column(if_part, data) + ")]"
            )
        elif variable == VAR_NOT_X:
            expressions[variable] = (
                DUNDER_DF + ".index[~(" + pandas_column(if_part, data) + ")]"
            )
        elif variable == VAR_Y:
            expressions[variable] = (
                DUNDER_DF + ".index[(" + pandas_column(then_part, data) + ")]"
            )
        elif variable == VAR_NOT_Y:
            expressions[variable] = (
                DUNDER_DF + ".index[~(" + pandas_column(then_part, data) + ")]"
            )
        elif variable == VAR_X_AND_Y:
            expressions[variable] = (
                DUNDER_DF
                + ".index[("
                + pandas_column(if_part, data)
                + ") & ("
                + pandas_column(then_part, data)
                + ")]"
            )
        elif variable == VAR_X_AND_NOT_Y:
            expressions[variable] = (
                DUNDER_DF
                + ".index[("
                + pandas_column(if_part, data)
                + ") & ~("
                + pandas_column(then_part, data)
                + ")]"
            )
        elif variable == VAR_NOT_X_AND_NOT_Y:
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

    This function searches for specific patterns in the string expression, particularly column names
    enclosed in curly braces `{}`.

    Parameters:
    ----------
    expression: str
        A string containing an expression with column names enclosed in curly braces `{}`. The expression
        may include additional parameters specifying the operation on the columns (e.g., direction and key).

    data: pd.DataFrame
        A Pandas DataFrame that is used to check the columns referenced in the expression. This DataFrame
        is used to verify if a column is a string, boolean, or datetime type, which influences how the expression is processed.

    Returns:
    --------
    str
        The modified expression where the columns have been processed based on their data type and any
        tolerance instruction present. The resulting string can be used for further operations or query execution.

    Example:
        >>> expression = '{"A"}'
        >>> result = ruleminer.pandas_column(expression)
        >>> print(result)
        "_df[A]"

        >>> expression = '{"A" + default}'
        >>> result = ruleminer.pandas_column(expression)
        >>> print(result)
        "_df[A] + 0.5*abs(_df[A].apply(_tol, args=('key',))))"

    Errors may occur if the expression is not correctly formatted or if column names do not exist in the DataFrame.

    Notes:
    ------
    - The expression should only contain `{}` for column names and not for other parts of the string.
    - Tolerance is applied if the column is numeric and satisfies the given conditions.
    - The output is a modified version of the original expression.

    """

    if expression == "()":
        return expression

    # new_expression = ""
    # idx = 0
    # while idx < len(expression):
    #     new_expression += expression[idx]
    #     if expression[idx] == "{":
    #         start = idx + 2
    #     elif expression[idx] == "}":
    #         end = idx - 1
    #         column = expression[start: end]
    #         if column in data.columns and (
    #            (not pd.api.types.is_string_dtype(data[column]))
    #             and (not pd.api.types.is_bool_dtype(data[column]))
    #             and (not pd.api.types.is_datetime64_ns_dtype(data[column]))
    #         ):
    #             if expression[end+2:end+13]==".apply(_tol":
    #                 apply_end = False
    #                 arg_end = False
    #                 while not apply_end:
    #                     if expression[idx] == ")":
    #                         if arg_end:
    #                             apply_end = True
    #                         else:
    #                             arg_end = True
    #                     idx += 1
    #     idx += 1
    return expression.replace('{"', DUNDER_DF + '["').replace('"}', '"]')


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
        "_df[(_df["A"] > 0)]"
    """
    if expression != "":
        expression = "[(" + pandas_column(expression, data) + ")]"
    return DUNDER_DF + expression
