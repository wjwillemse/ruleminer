"""Parser module."""

import re
import pyparsing
from typing import Dict

from .const import DUNDER_DF

_lpar, _rpar = map(pyparsing.Suppress, "()")
_lbra, _rbra = map(pyparsing.Suppress, "[]")
# _sep = pyparsing.Suppress(",")
_sep = pyparsing.Literal(",")
_number = pyparsing.Regex(r"[+-]?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?")
_function = pyparsing.one_of(
    "min \
    max \
    abs \
    quantile \
    sum \
    substr \
    split \
    count \
    sumif \
    countif \
    MIN \
    MAX \
    ABS \
    QUANTILE \
    SUM \
    SUBSTR \
    SPLIT \
    COUNT \
    SUMIF \
    COUNTIF"
)
_for = pyparsing.one_of("for", "FOR")
_in = pyparsing.one_of("in", "IN")
_empty = pyparsing.one_of(["None", '""', "pd.NA", "np.nan"])
_list_comprehension_var = pyparsing.Word(pyparsing.alphas)
_quote = pyparsing.Literal('"')
_string = (
    pyparsing.srange(r"[a-zA-Z0-9_.,:;<>*=+-/?|@#$%^&\[\]{}\(\)\\']")
    + " "
    + "\x01"
    + "\x02"
    + "\x03"
    + pyparsing.pyparsing_unicode.Greek.alphas
    + pyparsing.pyparsing_unicode.Greek.alphanums
)
_quoted_string = pyparsing.Combine(_quote + pyparsing.Word(_string) + _quote)
_column = pyparsing.Combine("{" + _quote + pyparsing.Word(_string) + _quote + "}")
_addop = pyparsing.Literal("+") | pyparsing.Literal("-")
_multop = pyparsing.Literal("*") | pyparsing.Literal("/")
_expop = pyparsing.Literal("**")
_compa_op = pyparsing.one_of(">= > <= < != == in IN")

_list_element = _quoted_string | _column | _number | _empty
_quoted_string_list = pyparsing.Group(
    _lbra + _list_element + (_sep + _list_element)[0, ...] + _rbra
) | pyparsing.Group(
    _lpar + _lbra + _list_element + (_sep + _list_element)[0, ...] + _rbra + _rpar
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
    expr = pyparsing.Forward()
    params = pyparsing.Forward()
    math_expr = math_expression(expr)
    param_element = (
        math_expr
        | _quoted_string_list
        | _quoted_string
        | _column
        | _number
        | _empty
        | _list_comprehension_var
    )
    param_condition = param_element + _compa_op + param_element

    param_condition_list = pyparsing.Group(
        _lbra
        + pyparsing.Group(param_condition)
        + (_sep + pyparsing.Group(param_condition))[...]
        + _rbra
    )
    param_condition_list_comprehension = pyparsing.Group(
        _lbra
        + pyparsing.Group(param_condition | param_element)
        + _for
        + _list_comprehension_var
        + _in
        + _lbra
        + pyparsing.Group(
            pyparsing.Group(_column) + (_sep + pyparsing.Group(_column))[...]
        )
        + _rbra
        + _rbra
    )
    param = (
        param_condition_list_comprehension
        | param_condition_list
        | param_condition
        | param_element
    )
    params <<= param + (_sep + param)[...]
    expr <<= pyparsing.Group(_function + pyparsing.Group(_lpar + params + _rpar))
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
    expr = pyparsing.Forward()
    if base is None:
        element = _quoted_string_list | _quoted_string | _column | _number | _empty
    else:
        element = (
            base | _quoted_string_list | _quoted_string | _column | _number | _empty
        )
    atom = element | pyparsing.Group(_lpar + expr + _rpar)
    factor = pyparsing.Forward()
    factor <<= atom + (_expop + factor)[...]
    term = factor + (_multop + factor)[...]
    expr <<= term + (_addop + term)[...]
    return expr


def condition_expression(base: pyparsing.core.Forward = None):
    """
    Define a ruleminer condition expression

    This function defines a ruleminer condition expression. It uses pyparsing to define
    the syntax for conditions and condition syntax

    Args:
        None

    Returns:
        pyparsing.core.Forward: a ruleminer condition expression

    Example:
        >>> expression = '({"A"} > 0)'
        >>> result = ruleminer.condition_expression().parse_string(expression)
        >>> print(result)
        [['{"A"}', '>', '0']]
    """
    condition_item = (
        math_expression(function_expression())
        + _compa_op
        + math_expression(function_expression())
    )
    comp_expr = pyparsing.Group(_lpar + condition_item + _rpar)
    condition = pyparsing.infixNotation(
        comp_expr,
        [
            (
                pyparsing.one_of(["NOT", "not", "~"]),
                1,
                pyparsing.opAssoc.RIGHT,
            ),
            (
                pyparsing.one_of(["AND", "and", "&"]),
                2,
                pyparsing.opAssoc.LEFT,
            ),
            (
                pyparsing.one_of(["OR", "or", "|"]),
                2,
                pyparsing.opAssoc.LEFT,
            ),
        ],
    )
    return condition


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

    if_expr = pyparsing.Forward()
    if_condition = condition_expression(if_expr)
    then_expr = pyparsing.Forward()
    then_condition = condition_expression(then_expr)
    if_then = (
        "if" + if_condition + "then" + then_condition
        | "IF" + if_condition + "THEN" + then_condition
    )
    rule_syntax = (
        if_then
        | "if () then " + then_condition
        | "IF () THEN " + then_condition
        | then_condition
    )
    return rule_syntax


def dataframe_lengths(expression: str = "", required: list = []) -> Dict[str, str]:
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
                expressions[variable] = "(" + pandas_column(if_part) + ").sum()"
        elif variable == "~X":
            expressions[variable] = "(~(" + pandas_column(if_part) + ")).sum()"
        elif variable == "Y":
            expressions[variable] = "(" + pandas_column(then_part) + ").sum()"
        elif variable == "~Y":
            expressions[variable] = "(~(" + pandas_column(then_part) + ")).sum()"
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
    return expression.replace("{", DUNDER_DF + "[").replace("}", "]")


def dataframe_values(expression: str = ""):
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
        expression = "[(" + pandas_column(expression) + ")]"
    return DUNDER_DF + expression
