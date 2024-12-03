"""Parser module."""

import pyparsing

# _lpar, _rpar = map(pyparsing.Suppress, "()")
# _lbra, _rbra = map(pyparsing.Suppress, "[]")
_lpar = pyparsing.Literal("(")
_rpar = pyparsing.Literal(")")
_lbra = pyparsing.Literal("[")
_rbra = pyparsing.Literal("]")
_sep = pyparsing.Literal(",")
_number = pyparsing.Regex(r"[+-]?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?")
_timedate_functions = pyparsing.one_of(
    "day_name \
    month_name \
    days_in_month \
    daysinmonth \
    is_leap_year \
    is_year_end \
    dayofweek \
    weekofyear \
    weekday \
    week \
    is_month_end \
    is_month_start \
    is_year_start \
    is_quarter_end \
    is_quarter_start \
    day \
    month \
    quarter \
    year \
    DAY_NAME \
    MONTH_NAME \
    DAYS_IN_MONTH \
    DAYSINMONTH \
    IS_LEAP_YEAR \
    IS_YEAR_END \
    DAYOFWEEK \
    WEEKOFYEAR \
    WEEKDAY \
    WEEK \
    IS_MONTH_END \
    IS_MONTH_START \
    IS_YEAR_START \
    IS_QUARTER_END \
    IS_QUARTER_START \
    DAY \
    MONTH \
    QUARTER \
    YEAR"
)
_timedelta_functions = pyparsing.one_of(
    "days \
    DAYS \
    months \
    MONTHS \
    years \
    YEARS"
)

_function = (
    pyparsing.one_of(
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
    | _timedelta_functions
    | _timedate_functions
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
    # + pyparsing.pyparsing_unicode.Greek.alphas
    # + pyparsing.pyparsing_unicode.Greek.alphanums
)
_quoted_string = pyparsing.Combine(_quote + pyparsing.Word(_string) + _quote)
_column = pyparsing.Combine("{" + _quote + pyparsing.Word(_string) + _quote + "}")
_addop = pyparsing.Literal("+") | pyparsing.Literal("-")
_multop = pyparsing.Literal("*") | pyparsing.Literal("/")
_expop = pyparsing.Literal("**")
_compa_op = pyparsing.one_of(">= > <= < != == in IN match MATCH")

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
    condition = simple_condition_expression()
    param_element = (
        math_expr
        | _quoted_string_list
        | _quoted_string
        | _column
        | _number
        | _empty
        | _list_comprehension_var
        | condition
    )
    param_condition = param_element + _compa_op + param_element

    param_condition_list = (
        _lbra + param_condition + (_sep + param_condition)[...] + _rbra
    )
    param_condition_list_comprehension = pyparsing.Group(
        _lbra
        + pyparsing.Group(param_condition | param_element)
        + _for
        + _list_comprehension_var
        + _in
        + (_lbra + _column + (_sep + _column)[...] + _rbra)
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
        element = (
            _quoted_string_list
            | _quoted_string
            | _column
            | _number
            | _list_comprehension_var
            | _empty
        )
    else:
        element = (
            base
            | _quoted_string_list
            | _quoted_string
            | _column
            | _number
            | _list_comprehension_var
            | _empty
        )
    atom = element | pyparsing.Group(_lpar + expr + _rpar)
    factor = pyparsing.Forward()
    factor <<= atom + (_expop + factor)[...]
    term = factor + (_multop + factor)[...]
    expr <<= term + (_addop + term)[...]
    return expr


def simple_condition_expression():
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
    left = pyparsing.Forward()
    right = pyparsing.Forward()
    condition_item = math_expression(left) + _compa_op + math_expression(right)
    comp_expr = pyparsing.Group(_lpar + condition_item + _rpar) | condition_item
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
