# Rule grammar

The rule template describes the structure of the rule. Columns and quoted strings in the rule template can contain simple regular expressions.

The syntax of the template follows a grammar defined as follows:

## General rule template format

* a *template* is of the form:
```
if cond_1 then cond_2
```
  or simply a single:
```
cond_1
```

* a *condition* is either a combination of *comparisons* with *logical operators* ('&' and '|') and parenthesis:
```
( comp_1 & comp_2 | comp_3 )
```

or simply a single *comparison*:
```
comp_1
```

* a *comparison* consists of a *term*, a *comparison operator* and a *term*, so::
```
term_1 > term_2
```

## Comparison operators

The following comparison operators are availabe:

* `>=`, `>`, `<=`, `<`, `!=`, `==` 
* `in` 
* `between`
* `match`
* `contains` 

## Terms: numbers, strings, columns, functions

* a `term` can be a `number` (e.g. +3, -4.1, 2.1e-8 and 0.9e10), `quoted string` (a string with single or double quotes), a `column` or a `function of columns`

* a `string` consists of the following characters: a-z A-Z 0-9 _ . , ; ; < > * = + - / \ ? | @ # $ % ^ & ( )

* a `column` is a `string` with braces, so:
```
{"Type"}
```

Here "Type" is the name of the column in the DataFrame with the data

* a `function of columns` is either a prefix operator (min, max, quantile, or abs, in lower or uppercase) on one or more *columns*, and of the form, for example:
```
min(col_1, col_2, col_3)
```
or infix operators with one or more columns:
```
(col_1 + col_2 * col_3)
```

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

* corr

* std

## String functions

* substr

* split

## Conditional functions

* sumif

* countif

## Functions for external data

* table

## Date and time functions

* days

* months

* years
 
## Full grammar

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

base_element = _quoted_string | _column | _number | _empty | _list_comprehension_var
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

_if_then = (
    "if" + condition_expression + "then" + condition_expression
    | "IF" + condition_expression + "THEN" + condition_expression
)

rule_expression = (
    _if_then
    | "if () then " + condition_expression
    | "IF () THEN " + condition_expression
    | condition_expression
)
```
