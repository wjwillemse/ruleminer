# Rule grammar

The rule grammar describes the syntactical requirements of rules that ruleminer can process.

## General rule format

The general rule format is `if condition_1 then condition_2` or simply a `condition`.

A `condition` is a logical expression of `comparisions` with `&`, `|` and `~` and parentheses, for example `cond_1 & (cond_2 | cond_3)`.

A single `comparision` consists of two `mathematical expressions` separated by a `comparison operator`, for example `math_expr_1 > math_expr_2`. The following comparison operators are availabe:

* `>=`, `>`, `<=`, `<`, `!=`, `==` 

* `in` and `not in`

* `between` and `not between`

* `match` and `not match`

* `contains` and `not contains`

A `mathematical expression` is an expression with `functions`, `base elements` and `lists` with mathematical operators `+`, `-`, `*`, `/` and `**`. Mathematical expressions can be nested. A `function` is a function name followed by `parameters` separated by commas with parentheses around them. A `parameter` can be a `list`, `condition`, or a `mathematical expression`. Function names can be upper or lower cased.

The base elements are:

* `numbers` can be of the form +3, -4.1, 2.1e-8 and 0.9e10

* `quoted strings` consists of the following characters: a-z A-Z 0-9 _ . , ; ; < > * = + - / \ ? | @ # $ % ^ & ( ) with double parentheses

* `columns` of the dataset, i.e. `quoted string` with braces, for example `{"Type"}`

## General mathematical functions

* min

* max

* abs

* sum

## Rounding functions
 
* exact

* round

* floor

* ceil

## Statistical functions

* quantile

* mean

* std

* corr

## String functions

* `substr(s, pos, len)` returns the substring of `s` from position `pos` (starting at 1) with length `len`

* `split(s, sep, n)` returns the `n`-th element (starting at 1) of the list of elements of string `s` separated by `sep` 

## Conditional functions

* `sumif([a, b, ... ], cond)` returns the sum of list [a, b, ...] given that condition `cond` is satisfied

* `sumif([a, b, ... ], [cond_a, cond_b, ... ])` returns the sum of list [a, b, ...] given that the corresponding condition is satisfied. The length of the lists should be equal.

* `countif([a, b, ... ], cond)` returns the count of list [a, b, ...] given that condition `cond` is satisfied

* `countif([a, b, ... ], [cond_a, cond_b, ... ])` returns the count of list [a, b, ...] given that the corresponding condition is satisfied. The length of the lists should be equal.

## Functions for external data

* table

## Date and time functions

* days

* months

* years
 
# Full grammar in pyparsing

```
_lpar = pyparsing.Literal("(")
_rpar = pyparsing.Literal(")")
_lbra = pyparsing.Literal("[")
_rbra = pyparsing.Literal("]")
_sep = pyparsing.Literal(",")
_quote = pyparsing.Literal('"')
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
    year",
    caseless=True,
)
_timedelta_functions = pyparsing.one_of("days months years", caseless=True)

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
    mean \
    std \
    exact \
    corr \
    round \
    floor \
    ceil \
    table",
        caseless=True,
    )
    | _timedelta_functions
    | _timedate_functions
)
_for = pyparsing.one_of("for", caseless=True)
_in = pyparsing.one_of("in", caseless=True)
_empty = pyparsing.one_of(["None", '""', "pd.NA", "np.nan"])
_list_comprehension_var = pyparsing.Word(pyparsing.alphas)
_string = (
    pyparsing.srange(r"[a-zA-Z0-9_.,:;<>*=+-/?|@#$%^&\[\]{}\(\)\\']")
    + " "
    + "\x01"
    + "\x02"
    + "\x03"
)
_quoted_string = pyparsing.Combine(_quote + pyparsing.Word(_string) + _quote)
_column = pyparsing.Combine("{" + _quote + pyparsing.Word(_string) + _quote + "}")
_addop = pyparsing.one_of("+ -")
_multop = pyparsing.one_of("* /")
_expop = pyparsing.Literal("**")
_compa_op = (
    pyparsing.one_of(">= > <= < != == in between match contains", caseless=True)
    | pyparsing.CaselessLiteral("not in")
    | pyparsing.CaselessLiteral("not between")
    | pyparsing.CaselessLiteral("not match")
    | pyparsing.CaselessLiteral("not contains")
)
base_element = (
    _quoted_string 
    | _column 
    | _number 
    | _empty 
    | _list_comprehension_var
)
math_expression = pyparsing.Forward()
condition_expression = pyparsing.infixNotation(
    (math_expression + _compa_op + math_expression),
    [
        (
            pyparsing.one_of(["not", "~"], caseless=True),
            1,
            pyparsing.opAssoc.RIGHT,
        ),
        (
            pyparsing.one_of(["and", "&"], caseless=True),
            2,
            pyparsing.opAssoc.LEFT,
        ),
        (
            pyparsing.one_of(["or", "|"], caseless=True),
            2,
            pyparsing.opAssoc.LEFT,
        ),
    ],
    lpar=pyparsing.Literal("("),
    rpar=pyparsing.Literal(")"),
)
param = pyparsing.Forward()
list_expression = pyparsing.Group(_lbra + param + (_sep + param)[...] + _rbra)
list_comprehension_expression = pyparsing.Group(
    _lbra
    + pyparsing.Group(param)
    + _for
    + _list_comprehension_var
    + _in
    + list_expression
    + _rbra
)
param <<= (
    list_comprehension_expression
    | list_expression
    | condition_expression
    | math_expression
)
params = param + (_sep + param)[...]
function = pyparsing.Group(_function + pyparsing.Group(_lpar + params + _rpar))
atom = (
    function
    | list_expression
    | base_element
    | pyparsing.Group(_lpar + math_expression + _rpar)
)
factor = pyparsing.Group(atom + pyparsing.OneOrMore(_expop + atom)) | atom
term = pyparsing.Group(factor + pyparsing.OneOrMore(_multop + factor)) | factor
math_expression <<= term + pyparsing.ZeroOrMore(_addop + term)

_if = pyparsing.one_of("if", caseless=True)
_then = pyparsing.one_of("then", caseless=True)
rule_expression = (
    _if + condition_expression + _then + condition_expression
    | "if () then " + condition_expression
    | "IF () THEN " + condition_expression
    | condition_expression
)
```
