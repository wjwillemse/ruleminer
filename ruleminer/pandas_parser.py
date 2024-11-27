"""Pandas parser module."""

import re
import pandas as pd
from typing import Dict
import logging

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
    enclosed in curly braces `{}`. If there is an additional instruction for tolerance (e.g., direction
    and key), it applies a custom operation. Specific data types (such as strings, booleans, and datetimes)
    are checked, and if the column's data type is neither of these types, a tolerance is applied in the calculation.

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
                # column does not contain the last "}", but key does
                if column[2:-1] not in data.columns:
                    logging.warning(
                        "Could not check the dtype of column "
                        + column[2:-1]
                        + " because it is not in the data DataFrame. Tolerances are not applied."
                    )
                if column[2:-1] in data.columns and (
                    (not pd.api.types.is_string_dtype(data[column[2:-1]]))
                    and (not pd.api.types.is_bool_dtype(data[column[2:-1]]))
                    and (not pd.api.types.is_datetime64_ns_dtype(data[column[2:-1]]))
                ):
                    # apply tolerance
                    column_expr = (
                        "("
                        + column
                        + "}"
                        + direction
                        + "0.5*abs("
                        + column
                        + "}"
                        + '.apply(_tol, args=("'
                        + key[:-1]
                        + '",)'
                        + ")))"
                    )
                    result = result[:start_column] + column_expr
                    offset += len(column_expr) - (end_column - start_column) - 1
                else:
                    # do not apply tolerance
                    result = result[:start_column] + column + "}"
                    offset += len(column) - (end_column - start_column)
            else:
                # does not contain tolerance, so add all
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
        "_df[(_df["A"] > 0)]"
    """
    if expression != "":
        expression = "[(" + pandas_column(expression, data) + ")]"
    return DUNDER_DF + expression
